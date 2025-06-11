from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import json
import csv
from collections import defaultdict
from pymongo import MongoClient  # добавляем MongoDB клиент

#Настройка подключения к MongoDB
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "namaz_db"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
col_grouped = db['users_grouped']  # коллекция для обработанных метрик
col_raw     = db['users_raw']      # коллекция для сырых данных

app = FastAPI(title="Dynamic Metrics Table")
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    """
    Главная страница с кнопкой для пересчёта метрик.
    """
    return templates.TemplateResponse(
        'index.html', {'request': request}
    )

@app.get('/metrics', response_class=HTMLResponse)
def metrics(request: Request):
    """
    Читает сырые данные, пересчитывает метрики по группам
    и отображает результат в виде HTML-таблицы.
    """
    # Загружаем пользователей
    with open('namaz_learners_anon.json', encoding='utf-8') as f:
        learners = json.load(f)
    learners_df = pd.DataFrame(learners)
    learners_df['_id'] = learners_df['_id'].astype(str)
    learners_df['launch_count'] = (
        pd.to_numeric(learners_df['launch_count'], errors='coerce')
          .fillna(0).astype(int)
    )

    # Загружаем логи
    with open('namaz_logs_anon (2).json', encoding='utf-8-sig') as f:
        logs = json.load(f)
    logs_df = pd.DataFrame(logs)
    logs_df['learner_id'] = logs_df['learner_id'].astype(str)

    # Сохраняем сырые данные в MongoDB
    raw_docs = learners_df.to_dict(orient='records')
    col_raw.delete_many({})
    if raw_docs:
        col_raw.insert_many(raw_docs)

    # Читаем outcomes для mastery
    outcome_map = defaultdict(list)
    with open('namaz_outcomes.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for assess in filter(None, map(str.strip, row['Assesses'].split(','))):
                outcome_map[row['Outcome ID']].append(assess)

    # group_size и динамический retention 
    grouped = learners_df.groupby('recommendation_method').agg(
        group_size=('_id', 'count')
    ).reset_index()
    launch_logs = logs_df[logs_df['activity_id'] == 'launch']
    retention = (
        launch_logs.groupby('learner_id').size().reset_index(name='launch_count')
            .merge(learners_df[['_id','recommendation_method']], left_on='learner_id', right_on='_id', how='left')
            .groupby('recommendation_method')['launch_count']
            .mean().reset_index(name='retention')
    )
    grouped = grouped.merge(retention, on='recommendation_method', how='left').fillna(0)

    # Engagement
    eng = (
        logs_df.groupby('learner_id').size().reset_index(name='log_count')
            .merge(learners_df[['_id','recommendation_method']], left_on='learner_id', right_on='_id', how='left')
            .groupby('recommendation_method')['log_count']
            .mean().reset_index(name='engagement')
    )

    # CTR 
    ctr_logs = logs_df[logs_df['activity_id'] == 'recommended_item_selected']
    ctr = (
        ctr_logs.groupby('learner_id').size().reset_index(name='ctr_clicks')
            .merge(learners_df[['_id','recommendation_method']], left_on='learner_id', right_on='_id', how='left')
            .groupby('recommendation_method')['ctr_clicks']
            .sum().reset_index()
    )

    # Mastery rate
    if 'value' in logs_df.columns:
        numeric = logs_df[logs_df['value'].apply(lambda x: isinstance(x, (int, float, str)) and str(x).replace('.', '', 1).isdigit())].copy()
        numeric['score'] = numeric['value'].astype(float)
        item_score = numeric.groupby(['learner_id', 'activity_id'])['score'].max().unstack(fill_value=0)
        item_score['mastery_score'] = item_score.apply(
            lambda row: sum(1 for items in outcome_map.values() if any(row.get(i, 0) > 0 for i in items)),
            axis=1
        )
        mastery = (
            item_score[['mastery_score']].reset_index()
                .merge(learners_df[['_id','recommendation_method']], left_on='learner_id', right_on='_id', how='left')
                .groupby('recommendation_method')['mastery_score']
                .mean().reset_index(name='mastery_rate')
        )
    else:
        mastery = grouped[['recommendation_method']].copy()
        mastery['mastery_rate'] = 0.0

    # Объединяем метрики 
    final = (
        grouped.merge(eng, on='recommendation_method', how='left')
               .merge(ctr, on='recommendation_method', how='left')
               .merge(mastery, on='recommendation_method', how='left')
               .fillna(0)
    )
    final['CTR'] = final['ctr_clicks'] / final['group_size']
    table = final[['recommendation_method','group_size','retention','engagement','CTR','mastery_rate']]

    # Сохраняем агрегаты в MongoDB
    agg_docs = table.to_dict(orient='records')
    col_grouped.delete_many({})
    if agg_docs:
        col_grouped.insert_many(agg_docs)

    # Выводим таблицу 
    html_table = table.to_html(classes='table table-striped', index=False)
    return templates.TemplateResponse(
        'metrics.html', {'request': request, 'table': html_table}
    )

