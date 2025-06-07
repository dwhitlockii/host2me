from pymongo import MongoClient
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.environ.get("MONGO_DB", "host2me")

_client = None

def get_collection():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[DB_NAME]["companies"]


def save_company(data: dict):
    col = get_collection()
    col.update_one({"Website URL": data["Website URL"]}, {"$set": data}, upsert=True)


def save_html(domain: str, html: str) -> str:
    os.makedirs("output/html", exist_ok=True)
    fname = domain.replace("/", "_") + ".html"
    path = os.path.join("output", "html", fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
