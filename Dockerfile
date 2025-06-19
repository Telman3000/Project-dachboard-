# Dockerfile
# ======================
# 1) Базовый образ с минимальным Python
FROM python:3.11-slim

# 2) Рабочая директория внутри контейнера
WORKDIR /app

# 3) Сначала копируем только файл с зависимостями,
#    чтобы Docker-кэш работал эффективнее
COPY requirements.txt .

# 4) Устанавливаем все зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 5) Копируем в контейнер:
#    - основной код приложения
#    - папку с шаблонами (templates/index.html, metrics.html и т.д.)
COPY main.py . 
COPY templates/ ./templates/

# 6) Переменная окружения (по умолчанию локальный MongoDB)
ENV MONGO_URI="mongodb://mongodb:27017/"
ENV PORT=8000

# 7) Открываем порт
EXPOSE 8000

# 8) Точка входа — наш main.py сам решит, uvicorn (Windows) или Gunicorn (Linux)
CMD ["python", "main.py"]
