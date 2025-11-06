from .database import get_db
from tinydb import Query

def update_feedback(url, new_feedback, graph_handler):
    db = get_db()
    article = Query()
    db.update({"feedback": new_feedback}, article.url == url)

    # Update graph based on new feedback
    graph_handler.update_feedback(url, new_feedback)


def update_notes(url, new_note):
    db = get_db()
    article = Query()
    db.update({"note": new_note}, article.url == url)


def add_feedback(url, new_note, new_feedback, graph_handler):
    db = get_db()
    article = Query()
    db.update({"note": new_note, "feedback": new_feedback}, article.url == url)

    # Update graph handler
    graph_handler.update_feedback(url, new_feedback)
