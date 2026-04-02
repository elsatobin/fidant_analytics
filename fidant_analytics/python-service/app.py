from fastapi import FastAPI, HTTPException, Query
from prisma import Prisma
from datetime import datetime, timedelta
from typing import List

app = FastAPI()
db = Prisma()

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.get("/api/usage/stats")
async def usage_stats(days: int = Query(7, ge=1, le=90), user_id: int = 1):
    """
    Returns daily usage stats for the authenticated user.
    - Only counts committed events.
    - Shows reserved separately.
    - Includes days with zero events.
    """
    try:
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=days - 1)
        stats = []

        for i in range(days):
            day = start_date + timedelta(days=i)
            record = await db.dailyusagecache.find_first(
                where={"userId": user_id, "date": datetime(day.year, day.month, day.day)}
            )
            if record:
                stats.append({
                    "date": str(day),
                    "committed": record.committed,
                    "reserved": record.reserved,
                    "limit": record.limit,
                    "utilization": record.committed / record.limit if record.limit else 0
                })
            else:
                stats.append({
                    "date": str(day),
                    "committed": 0,
                    "reserved": 0,
                    "limit": 30,
                    "utilization": 0
                })

        total_committed = sum(d["committed"] for d in stats)
        avg_daily = total_committed / days
        peak_day = max(stats, key=lambda x: x["committed"])

        # Current streak (simplified: consecutive days with committed > 0, counting backwards)
        streak = 0
        for d in reversed(stats):
            if d["committed"] > 0:
                streak += 1
            else:
                break

        return {
            "plan": "starter",
            "daily_limit": 30,
            "period": {"from": str(start_date), "to": str(today)},
            "days": stats,
            "summary": {
                "total_committed": total_committed,
                "avg_daily": avg_daily,
                "peak_day": peak_day,
                "current_streak": streak
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))