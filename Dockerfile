# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Скопировать только requirements и установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать всё приложение
COPY . .

# Переменные окружения
ENV MONGO_URI="mongodb://mongodb:27017/dashboard"
ENV PORT=8000

# Порт, на котором будет слушать Uvicorn
EXPOSE 8000

# Запускаем Uvicorn (не gunicorn — с ним были проблемы с ASGI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
