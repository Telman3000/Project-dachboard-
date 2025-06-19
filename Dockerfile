# Используем Uvicorn+ASGI, чтобы не сталкиваться с проблемой FastAPI.__call__
FROM python:3.11-slim
WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное
COPY . .

# Экспонируем порт
EXPOSE 8000

# Запускаем uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
