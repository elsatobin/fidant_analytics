import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, Depends, Query, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel

from db import Base, engine, get_db
import models
from auth import decode_token, create_access_token

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

PLAN_LIMITS: Dict[str, int] = {
    "starter": 30,
    "pro": 100,
    "executive": 500,
}

# Cache is considered fresh if written within the last 5 minutes.
# Past days are cached indefinitely (they can't change).
CACHE_TTL_SECONDS = 300


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization:
        raise HTTPException(status_code=401, detail={"error": "Missing token"})

    token = authorization.removeprefix("Bearer ")
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail={"error": "User not found"})

    return user


def generate_date_list(days: int) -> List[str]:
    today = datetime.utcnow().date()
    return [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in reversed(range(days))
    ]


def _is_today(date_key: str) -> bool:
    return date_key == datetime.utcnow().date().strftime("%Y-%m-%d")


def _fetch_committed_from_events(
    db: Session, user_id: int, date_keys: List[str]
) -> Dict[str, int]:
    """Query raw events table for committed counts on given dates."""
    rows = (
        db.query(models.DailyUsageEvent.date_key, func.count().label("count"))
        .filter(models.DailyUsageEvent.user_id == user_id)
        .filter(models.DailyUsageEvent.status == "committed")
        .filter(models.DailyUsageEvent.date_key.in_(date_keys))
        .group_by(models.DailyUsageEvent.date_key)
        .all()
    )
    return {r[0]: r[1] for r in rows}


def _upsert_cache(
    db: Session, user_id: int, date_key: str, committed: int, daily_limit: int
) -> None:
    """Write or refresh a cache row using upsert."""
    stmt = (
        pg_insert(models.DailyUsageCache)
        .values(
            user_id=user_id,
            date_key=date_key,
            committed=committed,
            daily_limit=daily_limit,
            cached_at=datetime.utcnow(),
        )
        .on_conflict_do_update(
            constraint="uq_cache_user_date",
            set_={
                "committed": committed,
                "daily_limit": daily_limit,
                "cached_at": datetime.utcnow(),
            },
        )
    )
    db.execute(stmt)
    db.commit()


def get_committed_map(
    db: Session, user_id: int, date_list: List[str], daily_limit: int
) -> Dict[str, int]:
    """
    Return committed counts per date_key.
    Strategy:
      - For past days: use cache if present, otherwise query events and populate cache.
      - For today: use cache only if cached_at is within CACHE_TTL_SECONDS, else re-query.
    """
    now = datetime.utcnow()
    staleness_cutoff = now - timedelta(seconds=CACHE_TTL_SECONDS)

    cached_rows = (
        db.query(models.DailyUsageCache)
        .filter(models.DailyUsageCache.user_id == user_id)
        .filter(models.DailyUsageCache.date_key.in_(date_list))
        .all()
    )
    cache_map: Dict[str, models.DailyUsageCache] = {r.date_key: r for r in cached_rows}

    result: Dict[str, int] = {}
    missing: List[str] = []

    for date_key in date_list:
        cached = cache_map.get(date_key)
        if cached is None:
            missing.append(date_key)
            continue

        # Today's cache is only valid within TTL
        if _is_today(date_key) and cached.cached_at < staleness_cutoff:
            missing.append(date_key)
            continue

        result[date_key] = cached.committed

    if missing:
        fresh = _fetch_committed_from_events(db, user_id, missing)
        for date_key in missing:
            count = fresh.get(date_key, 0)
            result[date_key] = count
            _upsert_cache(db, user_id, date_key, count, daily_limit)

    return result


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Invalid credentials"})
    token = create_access_token({"user_id": user.id})
    return {"access_token": token}


@app.get("/api/usage/stats")
def get_usage_stats(
    days: int = Query(7, ge=1, le=90),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = user.plan_tier
    daily_limit = PLAN_LIMITS.get(plan, 30)

    date_list = generate_date_list(days)
    start_date = date_list[0]
    end_date = date_list[-1]

    committed_map = get_committed_map(db, user.id, date_list, daily_limit)

    # Active reservations: status=reserved, reserved_at within last 15 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    reserved_rows = (
        db.query(models.DailyUsageEvent.date_key, func.count().label("count"))
        .filter(models.DailyUsageEvent.user_id == user.id)
        .filter(models.DailyUsageEvent.status == "reserved")
        .filter(models.DailyUsageEvent.reserved_at >= cutoff)
        .filter(models.DailyUsageEvent.date_key.in_(date_list))
        .group_by(models.DailyUsageEvent.date_key)
        .all()
    )
    reserved_map: Dict[str, int] = {r[0]: r[1] for r in reserved_rows}

    days_data = [
        {
            "date": d,
            "committed": committed_map.get(d, 0),
            "reserved": reserved_map.get(d, 0),
            "limit": daily_limit,
            "utilization": round(committed_map.get(d, 0) / daily_limit, 2) if daily_limit else 0,
        }
        for d in date_list
    ]

    total_committed = sum(day["committed"] for day in days_data)
    avg_daily = round(total_committed / days, 2)
    peak = max(days_data, key=lambda x: x["committed"])

    streak = 0
    for day in reversed(days_data):
        if day["committed"] > 0:
            streak += 1
        else:
            break

    return {
        "plan": plan,
        "daily_limit": daily_limit,
        "period": {"from": start_date, "to": end_date},
        "days": days_data,
        "summary": {
            "total_committed": total_committed,
            "avg_daily": avg_daily,
            "peak_day": {"date": peak["date"], "count": peak["committed"]},
            "current_streak": streak,
        },
    }


@app.get("/seed-user")
def seed_user(db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email="test@test.com").first()
    if not user:
        user = models.User(email="test@test.com", name="Test User", plan_tier="starter")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"user_id": user.id}
