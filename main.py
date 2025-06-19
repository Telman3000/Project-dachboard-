#!/usr/bin/env python3
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Подключение к MongoDB по переменным окружения
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/dashboard")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
try:
    client.server_info()
except Exception as e:
    raise RuntimeError(f"Не удалось подключиться к MongoDB: {e}")
db = client.get_default_database()

@app.get("/")
async def homepage(request: Request):
    """
    Отдаёт HTML-страницу с кнопкой «Create».
    Шаблон лежит в templates/metrics.html
    """
    return templates.TemplateResponse("metrics.html", {"request": request})

@app.get("/metrics")
async def metrics(start_date: str, end_date: str):
    """
    Возвращает JSON со статистикой за период [start_date, end_date].
    Формат дат: YYYY-MM-DD
    """
    try:
        # Проверяем, что даты валидны
        _ = datetime.fromisoformat(start_date)
        _ = datetime.fromisoformat(end_date)

        date_filter = {"date": {"$gte": start_date, "$lte": end_date}}

        # 1) Пользователи
        learners = list(db.users_learners.find(date_filter))
        # У каждого пользователя должно быть поле recommendation_method
        for u in learners:
            u["recommendation_method"] = u.get("recommendation_method")

        total_learners = len(learners)

        by_method: dict[str,int] = {}
        for u in learners:
            key = u["recommendation_method"] or "None"
            by_method[key] = by_method.get(key, 0) + 1

        # 2) Логи
        total_logs = db.users_logs.count_documents(date_filter)

        # 3) Outcomes
        total_outcomes = db.outcomes.count_documents(date_filter)

        return JSONResponse({
            "total_learners": total_learners,
            "learners_by_method": by_method,
            "total_logs": total_logs,
            "total_outcomes": total_outcomes,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
