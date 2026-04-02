from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    plan_tier = Column(String, default="starter")
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyUsageEvent(Base):
    __tablename__ = "daily_usage_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date_key = Column(String)  # YYYY-MM-DD
    request_id = Column(String)
    status = Column(String)  # reserved | committed
    reserved_at = Column(DateTime, default=datetime.utcnow)
    committed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)