# namaz_metrics_with_filter.py

import json
import csv
from collections import defaultdict

import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm

# --- НАСТРОЙКА ПОДКЛЮЧЕНИЯ К MongoDB ---
MONGO_URI = "mongodb://localhost:27017/"  # замените при необходимости
DB_NAME = "namaz_db"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
col_grouped = db['users_grouped']  # коллекция для агрегатов
col_raw     = db['users_raw']      # коллекция для сырых данных

# --- ПАРАМЕТРЫ ФИЛЬТРАЦИИ ПОЛЬЗОВАТЕЛЕЙ ---
# Укажите здесь свойства и значения, по которым нужно отфильтровать
filter_criteria = {
    # 'property_name': 'desired_value',
}

# --- 1. ЗАГРУЗКА И ПРЕОБРАЗОВАНИЕ ДАННЫХ УЧЕНИКОВ ---
print("1) Загружаем пользователей из namaz_learners_anon.json…")
with open('namaz_learners_anon.json', encoding='utf-8') as f:
    learners_data = json.load(f)
learners_df = pd.DataFrame(learners_data)

# Приводим _id к строке и launch_count к целому числу
learners_df['_id'] = learners_df['_id'].astype(str)
learners_df['launch_count'] = (
    pd.to_numeric(learners_df['launch_count'], errors='coerce')
      .fillna(0)
      .astype(int)
)

# --- 2. ФИЛЬТРАЦИЯ ПО СВОЙСТВАМ ---
if filter_criteria:
    print(f"2) Применяем фильтрацию: {filter_criteria}")
    for prop, val in filter_criteria.items():
        # Оставляем только строки, где колонка prop равна val
        learners_df = learners_df[learners_df[prop] == val]
    print(f"   Оставшихся пользователей: {len(learners_df)}")
else:
    print("2) Фильтрация не применена (filter_criteria пуст). Всех пользователей учитываем.")

# --- 3. СОХРАНЕНИЕ СЫРЫХ ДАННЫХ ---
print("3) Сохраняем сырые данные в MongoDB…")
col_raw.delete_many({})  # очищаем коллекцию
col_raw.insert_many(learners_df.to_dict(orient='records'))

# --- 4. ГРУППИРОВКА group_size и retention ---
print("4) Считаем group_size и retention…")
grouped = learners_df.groupby('recommendation_method').agg({
    '_id': 'count',          # число пользователей в группе
    'launch_count': 'mean',  # среднее число запусков
}).rename(columns={
    '_id': 'group_size',
    'launch_count': 'retention'
}).reset_index()

# --- 5. ЗАГРУЗКА ЛОГОВ И ОГРАНИЧЕНИЕ ПО ОТФИЛЬТРОВАННЫМ ПОЛЬЗОВАТЕЛЯМ ---
print("5) Загружаем логи и фильтруем по пользователям…")
with open('namaz_logs_anon.json', encoding='utf-8-sig') as f:
    raw = f.read()
    logs = json.loads(raw)
logs_df = pd.DataFrame(logs)
logs_df['learner_id'] = logs_df['learner_id'].astype(str)
# Оставляем логи только для отфильтрованных пользователей
logs_df = logs_df[logs_df['learner_id'].isin(learners_df['_id'])]

# --- 6. ВЫЧИСЛЕНИЕ engagement (среднее число событий) ---
print("6) Считаем engagement…")
eng_counts = (
    logs_df.groupby('learner_id')
           .size()
           .reset_index(name='log_count')
)
eng_counts = eng_counts.merge(
    learners_df[['_id', 'recommendation_method']],
    left_on='learner_id', right_on='_id', how='left'
)
engagement = (
    eng_counts.groupby('recommendation_method')['log_count']
              .mean()
              .reset_index(name='engagement')
)

# --- 7. ВЫЧИСЛЕНИЕ CTR ---
print("7) Считаем CTR…")
ctr_logs = logs_df[logs_df['activity_id'] == 'recommended_item_selected']
ctr_counts = (
    ctr_logs.groupby('learner_id')
            .size()
            .reset_index(name='ctr_clicks')
)
ctr_counts = ctr_counts.merge(
    learners_df[['_id', 'recommendation_method']],
    left_on='learner_id', right_on='_id', how='left'
)
ctr = (
    ctr_counts.groupby('recommendation_method')['ctr_clicks']
              .sum()
              .reset_index()
)

# --- 8. ВЫЧИСЛЕНИЕ mastery_rate ---
print("8) Считаем mastery_rate…")
outcome_to_assess = defaultdict(list)
with open('namaz_outcomes.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        outcome = row['Outcome ID']
        for assess in filter(None, map(str.strip, row['Assesses'].split(','))):
            outcome_to_assess[outcome].append(assess)
# Оставляем логи с числовыми значениями
numeric_logs = logs_df[
    logs_df['value'].apply(
        lambda x: isinstance(x, (int, float, str)) and str(x).replace('.', '', 1).isdigit()
    )
].copy()
numeric_logs['score'] = numeric_logs['value'].astype(float)
learner_item_score = (
    numeric_logs.groupby(['learner_id', 'activity_id'])['score']
                .max()
                .unstack(fill_value=0)
)
# Функция подсчёта mastery для строки пользователя
def compute_mastery(row):
    passed = 0
    for items in outcome_to_assess.values():
        if any(row.get(item, 0) > 0 for item in items):
            passed += 1
    return passed
learner_item_score['mastery_score'] = learner_item_score.apply(compute_mastery, axis=1)
mastery_df = learner_item_score[['mastery_score']].reset_index().merge(
    learners_df[['_id', 'recommendation_method']],
    left_on='learner_id', right_on='_id', how='left'
)
mastery_rate = (
    mastery_df.groupby('recommendation_method')['mastery_score']
              .mean()
              .reset_index(name='mastery_rate')
)

# --- 9. СБОРКА ФИНАЛЬНОЙ ТАБЛИЦЫ ---
print("9) Объединяем метрики и сохраняем результат…")
final = (
    grouped
    .merge(engagement, on='recommendation_method', how='left')
    .merge(ctr, on='recommendation_method', how='left')
    .merge(mastery_rate, on='recommendation_method', how='left')
    .fillna(0)
)
final['CTR'] = final['ctr_clicks'] / final['group_size']
final = final[
    ['recommendation_method', 'group_size', 'retention', 
     'engagement', 'CTR', 'mastery_rate']
]

# --- 10. СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ---
col_grouped.delete_many({})
col_grouped.insert_many(final.to_dict(orient='records'))
final.to_csv('group_summary.csv', index=False)

print("Готовая таблица метрик по группам:")
print(final)
