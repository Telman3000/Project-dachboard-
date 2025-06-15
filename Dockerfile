FROM python:3.11-slim

WORKDIR /app

# Сначала копируем только requirements.txt, чтобы кэш Docker-а не сбрасывался при любом изменении кода
COPY requirements.txt .

# Обновляем pip и ставим зависимости
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# отмечаем, что внутри контейнера мы слушаем 8000-й порт
EXPOSE 8000  

# запускаем Uvicorn на 0.0.0.0:8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
