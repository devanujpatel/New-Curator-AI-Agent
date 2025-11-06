from news_data.fetcher.newsapi import fetch_newsapi_articles
from news_data.ranker import text_interest_scorer
from news_data.ranker import similar_article_scorer
from news_data.entity_recognition import extract_entities_gliner
from news_data.theme_detector import detect_themes_zeroshot
from news_data.helper.generate_article_id import generate_uuid_article_id
from datetime import datetime

today = datetime.now().strftime("%m/%d/%Y")


def init_score(article, liked_embeddings):
    article_embedding = article["embedding"]

    article["interest_score"] = text_interest_scorer.text_interest_score(article_embedding)
    article["liking_score"] = similar_article_scorer.similar_article_score(article_embedding,
                                                                           liked_embeddings)

def final_scorer(article, graph_handler):
    article["graph_score"] = graph_handler.graph_score(article["_id"])

    article["final_score"] = 0.4 * article["interest_score"] + 0.4 * article["liking_score"] + 0.2 * \
                             article["graph_score"]


def get_articles(inputs, articles_db, embedder, graph_handler):
    all_today_articles_list = articles_db.get_all_today_articles()
    print(f"fetched {len(all_today_articles_list)} articles from database")

    if len(all_today_articles_list) > 5:

        articles_dict = {}
        for article in all_today_articles_list:
            articles_dict[article["_id"]] = article

        return articles_dict

    api_articles_list = fetch_newsapi_articles(inputs)
    api_articles_dict = {}

    liked_embeddings = articles_db.get_liked_embeddings()

    for article in api_articles_list:
        embedding = embedder.get_article_embedding(article)

        new_article_id = generate_uuid_article_id()

        article["_id"] = new_article_id
        article["embedding"] = embedding
        article["reaction"] = "skipped"
        article["note"] = "skipped"
        article["date"] = datetime.now()

        init_score(article, liked_embeddings)

        # only process article if initial scores are above threshold
        if article["interest_score"] + article["liking_score"] > 20:
            title = article.get("title") or ""
            description = article.get("description") or ""

            entities = extract_entities_gliner(title + " " + description)
            themes = detect_themes_zeroshot(title + " " + description)

            article["entities"] = entities
            article["themes"] = themes

            graph_handler.add_article_node(new_article_id, article, embedding, entities, themes)

            final_scorer(article, graph_handler)
            api_articles_dict[new_article_id] = article

    articles_db.bulk_add_articles(api_articles_dict.values())

    all_today_articles = dict(sorted(
        api_articles_dict.items(),
        key=lambda item: item[1]["final_score"],
        reverse=True
    ))

    return all_today_articles

# TODO: idea: get all relevant articles about a company for fundamental analysis
