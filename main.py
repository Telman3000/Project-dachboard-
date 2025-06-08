from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from app.routers.users import router as users_router

app = FastAPI()

# Раздаём статику
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def root():
    html = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

# Подключаем роутер пользователей
app.include_router(users_router)
