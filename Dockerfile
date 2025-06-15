FROM python:3.11-slim

# 1) задаём рабочую директорию
WORKDIR /app

# 2) копируем только список зависимостей и сразу ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) копируем весь проект (main.py, templates/, *.json и пр.)
COPY . .

# 4) по-умолчанию запускаем Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
