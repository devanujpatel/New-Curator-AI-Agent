from datetime import datetime, timedelta

import pymongo
from bson import ObjectId
from news_data.db.database import Database


class ArticleDB:
    def __init__(self, db: Database):
        self.db = db
        self.articles = db.articles

    # ---------- Utility ----------
    @staticmethod
    def _today_range():
        """Return start (midnight) and end (next midnight) for today."""
        start = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        start = start - timedelta(days=1)
        end = start + timedelta(days=1)
        return start, end

    # ---------- Insert ----------
    def bulk_add_articles(self, articles):
        result = self.articles.insert_many(articles, ordered=False)
        print(f"Inserted {len(result.inserted_ids)}/{len(articles)} articles.")


    def add_article(self, url, title, description, category, embedding):
        if self.articles.find_one({"url": url}):
            return False

        result = self.articles.insert_one({
            "date": datetime.now(),   # store full timestamp
            "url": url,
            "title": title,
            "description": description,
            "category": category,
            "embedding": embedding,
            "reaction": "skipped",
            "note": "skipped",
        })
        return result.inserted_id

    def add_article_scores(self, article_id, interest_score, liking_score, graph_score, final_score, entities, themes):
        self.articles.update_one(
            {"_id": article_id},
            {"$set": {
                "interest_score": interest_score,
                "liking_score": liking_score,
                "graph_score": graph_score,
                "final_score": final_score,
                "entities": entities,
                "themes": themes
            }}
        )

    # ---------- Fetch ----------
    def fetch_article_by_url(self, url):
        return self.articles.find_one({"url": url})

    def get_all_articles(self):
        return list(self.articles.find().sort("date", pymongo.ASCENDING))

    def get_articles_by_ids(self, ids: list[ObjectId]):
        return list(self.articles.find({"_id": {"$in": ids}}))

    def get_today_articles_by_category(self, category: str):
        """Fetch today's articles for a category, sorted by final_score desc (uses index)."""
        start, end = self._today_range()
        return list(self.articles.find(
            {"date": {"$gte": start, "$lt": end}, "category": category}
        ).sort("final_score", -1))   # index-optimized sort

    def get_all_today_articles(self):
        """Fetch all today's articles, sorted by final_score desc (uses index)."""
        start, end = self._today_range()
        return list(self.articles.find(
            {"date": {"$gte": start, "$lt": end}}
        ).sort("final_score", -1))   # index-optimized sort

    # ---------- Update ----------
    def update_embedding(self, article_id, new_embedding):
        self.articles.update_one({"_id": article_id}, {"$set": {"embedding": new_embedding}})

    def get_liked_embeddings(self):
        liked_articles = self.articles.find({
            "reaction": {"$in": ["like", "love"]}
        })
        return [a["embedding"] for a in liked_articles]

    def get_feedback_note(self, url):
        article = self.fetch_article_by_url(url)
        if article:
            return {"reaction": article.get("reaction"), "note": article.get("note")}
        return None

    # ---------- Delete ----------
    def delete_today_articles(self):
        start, end = self._today_range()
        self.articles.delete_many({"date": {"$gte": start, "$lt": end}})



    # todo:
    # issues to fix
    # bad ner - for now done
    # too little articles (do top k best instead of threshold) - init threshold lowered
    # add deep dive feature
    # change how articles are retrieved to keep fresh ones coming
    # do heavy tasks in async
    # try hybrid ner methods (gliner + zero shot)

    