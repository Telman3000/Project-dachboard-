# Используем slim-образ Python 3.11
FROM python:3.11-slim

# Рабочая директория приложения
WORKDIR /app

# Копируем список зависимостей и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY main.py .
COPY import_data.py .
COPY namaz_learners_anon.json .
COPY namaz_logs_anon.json .
COPY namaz_outcomes.csv .
COPY app_structure.json .
COPY templates/ ./templates/

# Переменные окружения
ENV MONGO_URI="mongodb://mongodb:27017/dashboard"
ENV PORT=8000

# Открываем порт
EXPOSE 8000

# Запускаем через Gunicorn+UvicornWorker
CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--log-level", "info"]
