from pathlib import Path
from dotenv import load_dotenv
import os

# путь до корня проекта
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "ai_analytics")
