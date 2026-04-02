from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import Base, engine, get_db
import models

app = FastAPI()

# 🔥 테이블 자동 생성
Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "API is running"}


@app.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    result = db.query(models.DailyUsageEvent).all()
    return {"count": len(result)}