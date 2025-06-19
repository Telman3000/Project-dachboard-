#!/usr/bin/env python3
import argparse
import json
import csv
from pymongo import MongoClient

def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_csv(path):
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mongo-uri', required=True, help='MongoDB URI, e.g. mongodb://localhost:27017/dashboard')
    args = parser.parse_args()

    client = MongoClient(args.mongo_uri)
    db = client.get_default_database()

    # 1. users_learners
    users_learners = load_json('namaz_learners_anon.json')
    for doc in users_learners:
        # **ГАРАНТИЯ** поля recommendation_method
        if 'recommendation_method' not in doc:
            doc['recommendation_method'] = None
        db.users_learners.replace_one({'_id': doc['_id']}, doc, upsert=True)
    print(f"✔ Loaded {len(users_learners)} documents into 'users_learners'")

    # 2. users_logs
    users_logs = load_json('namaz_logs_anon.json')
    for doc in users_logs:
        if 'recommendation_method' not in doc:
            doc['recommendation_method'] = None
        db.users_logs.replace_one({'_id': doc['_id']}, doc, upsert=True)
    print(f"✔ Loaded {len(users_logs)} documents into 'users_logs'")

    # 3. outcomes
    outcomes = load_csv('namaz_outcomes.csv')
    for rec in outcomes:
        db.outcomes.replace_one({'id': rec['id']}, rec, upsert=True)
    print(f"✔ Loaded {len(outcomes)} records into 'outcomes'")

    # 4. app_structure
    app_struct = load_json('app_structure.json')
    for doc in app_struct:
        db.app_structure.replace_one({'_id': doc['_id']}, doc, upsert=True)
    print(f"✔ Loaded {len(app_struct)} documents into 'app_structure'")

    print("\n✅ All data successfully imported into MongoDB.")

if __name__ == '__main__':
    main()
