from news_data.fetcher.newsapi import fetch_newsapi_articles
from news_data.db.migration.old_tindydb_files import feedback as fb
from news_data.ranker import embedder
from datetime import datetime
from news_data.ranker import sorter
from news_data.ranker import graph_handler

today = datetime.today().strftime("%m-%d-%Y")

API_KEY = "8edc4ac0af97446ca93446a5d872169f"

inputs = {
    "country": "us",
    "categories": ["business", "technology"],
    "page_size": 30
}

embedder = embedder.EmbeddingService()
graph_handler = graph_handler.GraphHandler()

# gets articles for today for each category
# returns articles, stored or new based on day and category
articles_list = fetch_newsapi_articles(inputs, API_KEY, embedder, graph_handler)

print(f"[INFO]: Fetched {len(articles_list)} articles")

ranked_articles = sorter.sort_articles(articles_list, graph_handler)

print("\nYour AI-Curated Top 5 Headlines Today:\n")
top_articles = ranked_articles[:5]

for idx, a in enumerate(top_articles, 1):
    print(f"{idx}. {a['title']}")
    print(f"   {a['url']}\n")

print("\nProvide feedback: love / like / dislike / skip")
for idx, article in enumerate(top_articles, 1):
    feedback = input(f"Feedback for article {idx}? (love/like/dislike/skip): ").strip().lower()
    if feedback in ["love", "like", "dislike"]:
        notes = input("Any notes about why? (optional): ").strip()
        fb.add_feedback(article["url"], notes, feedback, embedder, graph_handler)
        graph_handler.update_feedback(article["id"], feedback)
        print(f"Saved feedback: {feedback} | Notes: {notes}\n")
    else:
        print("Skipped.\n")

