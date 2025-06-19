#!/usr/bin/env python
import argparse
import json
import csv
from pymongo import MongoClient

def load_json_collection(db, filename, collection_name):
    with open(filename, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    col = db[collection_name]
    col.drop()
    col.insert_many(docs)
    print(f"✔ Loaded {len(docs)} documents into '{collection_name}'")

def load_csv_collection(db, filename, collection_name):
    with open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        docs = list(reader)
    col = db[collection_name]
    col.drop()
    col.insert_many(docs)
    print(f"✔ Loaded {len(docs)} records into '{collection_name}'")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mongo-uri", required=True)
    args = p.parse_args()

    client = MongoClient(args.mongo_uri)
    db = client.get_default_database()

    # Загрузить ваши JSON/CSV файлы
    load_json_collection(db, "namaz_learners_anon.json", "users_learners")
    load_json_collection(db, "namaz_logs_anon.json",     "users_logs")
    load_csv_collection(db,  "namaz_outcomes.csv",       "outcomes")
    load_json_collection(db, "app_structure.json",       "app_structure")

    # Гарантируем, что у каждого пользователя есть поле recommendation_method
    users = db.users_learners.find({})
    for u in users:
        if "recommendation_method" not in u:
            db.users_learners.update_one(
                {"_id": u["_id"]},
                {"$set": {"recommendation_method": None}}
            )
    print("✔ Filled missing 'recommendation_method' with None")

    print("✅ All data successfully imported into MongoDB.")
