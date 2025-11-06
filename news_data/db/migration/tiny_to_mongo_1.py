from pymongo import MongoClient
from news_data.db.migration.old_tindydb_files.database import get_db

# Load TinyDB data
db = get_db()
all_docs = db.all()

# Connect to MongoDB (default local instance)
client = MongoClient("mongodb://localhost:27017/")

# Select your database and collection
mongo_db = client["AURA"]
collection = mongo_db["all_articles"]

# Insert into MongoDB
if all_docs:
    collection.insert_many(all_docs)

print(f"Migrated {len(all_docs)} documents to MongoDB.")
