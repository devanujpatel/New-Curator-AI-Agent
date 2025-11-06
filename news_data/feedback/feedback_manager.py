import json
import os
from sentence_transformers import SentenceTransformer
import tinydb

FEEDBACK_FILE = "article_feedback_tinydb.json"
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

db = tinydb.TinyDB(FEEDBACK_FILE)

def save_feedback(article, feedback, notes=""):
    """
    Save user feedback (love, like, dislike) for an article.
    """
    if feedback not in ["love", "like", "dislike"]:
        raise ValueError("Feedback must be 'love', 'like', or 'dislike'")

    new_feedback = {
        "key": article["url"],
        "title": article["title"],
        "url": article["url"],
        "reaction": feedback,
        "notes": notes
    }

    db.insert(new_feedback)


def load_feedback_embeddings():
    """
    Returns two lists of embeddings: liked/loved and disliked.
    """
    if not os.path.exists(FEEDBACK_FILE):
        return [], []

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            feedback_data = json.loads(content) if content else {}
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = {}

    liked_embeddings, disliked_embeddings = [], []

    for entry in feedback_data.values():
        text = entry["title"] + " " + entry.get("notes", "")
        embedding = model.encode(text, convert_to_tensor=True)

        if entry["feedback"] in ("love", "like"):
            liked_embeddings.append(embedding)
        else:
            disliked_embeddings.append(embedding)

    return liked_embeddings, disliked_embeddings
