from pymongo import MongoClient

class Database:
    def __init__(self, db_name="AURA", uri="mongodb://localhost:27017/", article_collection="all_articles_layered"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.articles = self.db[article_collection]

    def close(self):
        self.client.close()
