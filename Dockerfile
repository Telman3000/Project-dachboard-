# ./Dockerfile
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Сначала копируем только requirements — чтобы не пересобирать всё при каждом изменении кода
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное
COPY . .

# Порт, который слушает Uvicorn
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
