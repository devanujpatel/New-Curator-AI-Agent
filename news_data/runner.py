from news_data.fetcher.newsapi import fetch_newsapi_articles
from news_data.ranker.old.article_ranker import rank_articles
from sentence_transformers import SentenceTransformer

API_KEY = "8edc4ac0af97446ca93446a5d872169f"

inputs = {
    "country": "us",
    "categories": ["business", "technology"],
    "page_size": 50
}

articles = fetch_newsapi_articles(inputs, API_KEY)

embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# articles = fetched + base score computed
ranked_articles = rank_articles(articles, embedding_model)

# Print top 5
for idx, a in enumerate(ranked_articles[:10], 1):
    print(f"{idx}. {a['title']} ({a['final_score']:.3f})")


# articles.sort(key=lambda x: x["score"], reverse=True)
# top_articles = articles[:5]
#
# for article in top_articles:
#     content = fetch_full_article_content(article["url"])
#     article["content"] = content
#     article["summary"] = create_ai_summary(content)
#
# print("\nYour AI-Curated Headlines with Summaries:\n")
# for idx, a in enumerate(top_articles, 1):
#     print(f"{idx}. {a['title']} ({a['score']:.3f})")
#     print(f"Summary: {a['summary']}")
#     print(f"URL: {a['url']}\n")