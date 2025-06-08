# backend/app/services/mongodb.py

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.config import MONGO_URI, MONGO_DB    # <-- импортируем сразу из config.py

# инициализируем клиент и базу из config.py
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
users_coll = db.get_collection("users")

async def fetch_users():
    return await users_coll.find().to_list(length=None)

async def find_user_by_email(email: str):
    return await users_coll.find_one({"email": email})

async def add_user(user_data: dict):
    result = await users_coll.insert_one(user_data)
    user_data["id"] = str(result.inserted_id)
    user_data.pop("_id", None)
    return user_data

async def delete_user(user_id: str):
    result = await users_coll.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count
