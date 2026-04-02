from fastapi import FastAPI, Depends, Query, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from pydantic import BaseModel  # ✅ 추가

from db import Base, engine, get_db
import models
from auth import decode_token, create_access_token
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev 서버 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

PLAN_LIMITS = {
    "starter": 30,
    "pro": 100,
    "executive": 500
}

# 🔐 JWT에서 사용자 가져오기
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# 🔧 날짜 생성
def generate_dates(days: int):
    today = datetime.utcnow().date()
    return [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in reversed(range(days))
    ]

# ✅ Pydantic 모델 정의
class LoginRequest(BaseModel):
    email: str

# 🔐 로그인 엔드포인트
@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id})
    return {"access_token": token}

# 🔹 Usage stats 엔드포인트
@app.get("/api/usage/stats")
def get_usage_stats(
    days: int = Query(7, ge=1, le=90),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = user.plan_tier
    daily_limit = PLAN_LIMITS.get(plan, 30)

    date_list = generate_dates(days)
    start_date = date_list[0]
    end_date = date_list[-1]

    # committed
    committed_rows = (
        db.query(models.DailyUsageEvent.date_key, func.count().label("count"))
        .filter(models.DailyUsageEvent.user_id == user.id)
        .filter(models.DailyUsageEvent.status == "committed")
        .filter(models.DailyUsageEvent.date_key.between(start_date, end_date))
        .group_by(models.DailyUsageEvent.date_key)
        .all()
    )
    committed_map = {r[0]: r[1] for r in committed_rows}

    # reserved (15분 이내)
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    reserved_rows = (
        db.query(models.DailyUsageEvent.date_key, func.count().label("count"))
        .filter(models.DailyUsageEvent.user_id == user.id)
        .filter(models.DailyUsageEvent.status == "reserved")
        .filter(models.DailyUsageEvent.reserved_at >= cutoff)
        .filter(models.DailyUsageEvent.date_key.between(start_date, end_date))
        .group_by(models.DailyUsageEvent.date_key)
        .all()
    )
    reserved_map = {r[0]: r[1] for r in reserved_rows}

    # days
    days_data = []
    for d in date_list:
        committed = committed_map.get(d, 0)
        reserved = reserved_map.get(d, 0)
        days_data.append({
            "date": d,
            "committed": committed,
            "reserved": reserved,
            "limit": daily_limit,
            "utilization": round(committed / daily_limit, 2) if daily_limit else 0
        })

    # summary
    total_committed = sum(d["committed"] for d in days_data)
    avg_daily = round(total_committed / days, 2) if days else 0
    peak_day = max(days_data, key=lambda x: x["committed"]) if days_data else None
    streak = 0
    for d in reversed(days_data):
        if d["committed"] > 0:
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
            "peak_day": {
                "date": peak_day["date"],
                "count": peak_day["committed"]
            } if peak_day else None,
            "current_streak": streak
        }
    }

# 🔹 Seed user
@app.get("/seed-user")
def seed_user(db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email="test@test.com").first()
    if not user:
        user = models.User(email="test@test.com", name="Test User", plan_tier="starter")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"user_id": user.id}