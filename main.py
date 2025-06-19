#!/usr/bin/env python3
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient

# 1) Инициализируем FastAPI и шаблонизатор
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 2) Подключаемся к MongoDB по переменной окружения
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/dashboard")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
try:
    # проверка соединения
    client.server_info()
except Exception as e:
    raise RuntimeError(f"Не удалось подключиться к MongoDB: {e}")
db = client.get_default_database()

# 3) Главная страница — просто отдаёт HTML с кнопкой Create
@app.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse("metrics.html", {"request": request})

# 4) Эндпоинт /metrics?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
@app.get("/metrics")
async def metrics(start_date: str, end_date: str):
    try:
        # откуда берём диапазон: ожидаем, что в коллекциях есть поле "date" в формате "YYYY-MM-DD"
        date_filter = {"date": {"$gte": start_date, "$lte": end_date}}

        # 4.1) Learners
        learners = list(db.users_learners.find(date_filter))
        # если вдруг нет поля recommendation_method — создаём с None
        for u in learners:
            u["recommendation_method"] = u.get("recommendation_method", None)

        # базовые метрики
        total_learners = len(learners)

        # группировка по recommendation_method
        by_method: dict[str,int] = {}
        for u in learners:
            key = u["recommendation_method"] or "None"
            by_method[key] = by_method.get(key, 0) + 1

        # 4.2) Logs
        total_logs = db.users_logs.count_documents(date_filter)

        # 4.3) Outcomes
        total_outcomes = db.outcomes.count_documents(date_filter)

        # собираем итоговый JSON
        result = {
            "total_learners": total_learners,
            "learners_by_method": by_method,
            "total_logs": total_logs,
            "total_outcomes": total_outcomes,
        }
        return JSONResponse(content=result)
    except Exception as e:
        # в случае ошибки — вернём 500 и текст
        raise HTTPException(status_code=500, detail=str(e))
