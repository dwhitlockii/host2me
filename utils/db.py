from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
import time

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.environ.get("MONGO_DB", "host2me")

_client = None

def _connect():
    global _client
    attempts = 0
    delay = 1
    while attempts < 5:
        try:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            _client.admin.command('ping')
            print("[DB] Connected successfully")
            return
        except Exception as e:
            attempts += 1
            print(f"[DB] Reconnect attempt {attempts} failed: {e}")
            time.sleep(delay)
            delay *= 2
    _client = None

def get_collection():
    global _client
    if _client is None:
        _connect()
    return _client[DB_NAME]["companies"] if _client else None


def save_company(data: dict):
    col = get_collection()
    if col:
        col.update_one({"Website URL": data["Website URL"]}, {"$set": data}, upsert=True)
    else:
        print("[DB] Skipping save, no database connection")


def save_html(domain: str, html: str) -> str:
    os.makedirs("output/html", exist_ok=True)
    fname = domain.replace("/", "_") + ".html"
    path = os.path.join("output", "html", fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
