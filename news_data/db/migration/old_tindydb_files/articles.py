from newspaper import Article
from tinydb import Query
from .database import get_db
from datetime import date

# today = date.today().strftime("%m/%d/%Y")

from datetime import date, timedelta

today = date.today()
yesterday = today - timedelta(days=1)
today = yesterday.strftime("%m/%d/%Y")

def add_article(id, url, title, description, category, embedding):
    db = get_db()
    q = Query()

    if not db.contains(q.url == url):

        db.insert({
            "id": id,
            "date": today,
            "url": url,
            "title": title,
            "description": description,
            "category": category,
            "embedding": embedding,
            "feedback": "skipped",
            "note": "skipped"
        })
        return True

    return False

def fetch_article_by_url(url):
    db = get_db()
    return db.get(Query().url == url)

def get_all_articles():
    db = get_db()
    return db.all()

def get_articles_by_ids(ids: list[int]) -> list[dict]:
    """
    Given a list of article IDs stored in the 'id' field, return the corresponding articles.
    """
    db = get_db()
    Article = Query()
    articles = []
    for id_value in ids:
        doc = db.get(Article.id == id_value)  # match on the field
        if doc is not None:
            articles.append(doc)
    return articles


def get_today_articles_by_category(category: str):
    db = get_db()
    article = Query()
    return db.search((article.date == today) & (article.category == category))

def update_embedding(article_id, change_to):
    db = get_db()
    article = Query()
    db.update({'embedded': change_to}, article.id == article_id)

def get_liked_embeddings():
    db = get_db()
    article = Query()

    liked_articles = db.search((article.feedback == 'like') | (article.feedback == 'love'))
    embeddings = []
    for article in liked_articles:
        embeddings.append(article.embedding)

    return embeddings

def get_feedback_note(url):
    db = get_db()
    article = Query()
    article = db.get(article.url == url)
    return {"feedback": article.feedback, "note": article.note}


def delete_today_articles():
    db = get_db()
    article = Query()
    db.remove(article.date == today)

def get_all_today_article_ids():
    db = get_db()
    article = Query()
    return db.search((article.date == today))