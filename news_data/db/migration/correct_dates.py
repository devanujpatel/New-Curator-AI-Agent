from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["AURA"]
articles = db["all_articles"]

for doc in articles.find({"date": {"$type": "string"}}):
    try:
        # adjust format string if needed
        new_date = datetime.strptime(doc["date"], "%m/%d/%Y")

        articles.update_one(
            {"_id": doc["_id"]},
            {"$set": {"date": new_date}}
        )
    except Exception as e:
        print(f"Skipping {doc['_id']}: {e}")
