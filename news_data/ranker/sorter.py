from news_data.ranker import text_interest_scorer
from news_data.ranker import similar_article_scorer


def sort_articles(articles_dict, graph_handler, articles_db):

    ids_to_delete = []

    liked_embeddings = articles_db.get_liked_embeddings()

    for article in articles_dict.values():

        article_embedding = article["embedding"]

        article["raw_interest_score"] = text_interest_scorer.text_interest_score(article_embedding)
        article["liked_similarity_score"] = similar_article_scorer.similar_article_score(article_embedding, liked_embeddings)
        article["graph_score"] = graph_handler.graph_score(article["_id"])

        article["final_score"] = 0.4 * article["raw_interest_score"] + 0.4 * article["liked_similarity_score"] + 0.2 * article["graph_score"]

        if article["final_score"] < 10:
            ids_to_delete.append(article["_id"])

    for id in ids_to_delete:
        del articles_dict[id]

    return sorted(articles_dict.keys(), key=lambda x: articles_dict[x]['final_score'], reverse=True)
