from news_data.db.database import Database

class FeedbackDB:
    def __init__(self, db: Database):
        self.db = db
        self.articles = db.articles

    def update_reaction(self, url, new_feedback):
        self.articles.update_one({"url": url}, {"$set": {"reaction": new_feedback}})

    def update_notes(self, url, new_note):
        self.articles.update_one({"url": url}, {"$set": {"note": new_note}})

    def add_feedback(self, url, new_note, new_feedback):
        self.articles.update_one({"url": url}, {"$set": {"note": new_note, "reaction": new_feedback}})
        # if graph_handler:
        #     graph_handler.update_feedback(url, new_feedback)
