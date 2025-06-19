# Dockerfile
# 1. Берём лёгкий Python
FROM python:3.11-slim

# 2. Рабочая директория внутри контейнера
WORKDIR /app

# 3. Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем приложение и шаблоны
COPY main.py .
COPY templates/ ./templates/

# 5. Переменные по умолчанию (можно переопределить при запуске)
ENV MONGO_URI="mongodb://mongodb:27017/"  
ENV PORT=8000

# 6. Открываем порт
EXPOSE 8000

# 7. Точка входа — main.py сам поднимет gunicorn в продакшене или uvicorn локально
CMD ["python", "main.py"]
