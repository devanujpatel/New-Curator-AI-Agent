from news_data.db.articles import ArticleDB
from news_data.db.database import Database
from news_data.ranker.graph_handler import Neo4jGraphHandler
from news_data.ranker import embedder as embedder_module
from news_data.ranker import text_interest_scorer
from news_data.ranker import similar_article_scorer
from news_data.entity_recognition import extract_entities_gliner
from news_data.theme_detector import detect_themes_zeroshot

og_db = Database()
og_articles_db = ArticleDB(og_db)

new_db = Database("all_articles_layered")
new_articles_db = ArticleDB(new_db)

new_graph_handler = Neo4jGraphHandler("neo4j://127.0.0.1:7687", "neo4j", "PWD", "aura-articles-layered")

embedder = embedder_module.EmbeddingService()

all_old_articles = og_articles_db.get_all_articles()

liked_embeddings = []

add_to_new = []
pruned = 0
for old_article in all_old_articles:
    # _id, url, desc, date, reaction, note, category, title
    # embedding, interest score, liking score, graph score, final_score

    old_article["embedding"] = embedder.get_article_embedding(old_article)

    if old_article["reaction"] in ["like", "love"]:
        liked_embeddings.append(old_article["embedding"])

    old_article["interest_score"] = text_interest_scorer.text_interest_score(old_article["embedding"])
    old_article["similarity_score"] = similar_article_scorer.similar_article_score(old_article["embedding"],
                                                                                   liked_embeddings)

    if old_article["interest_score"] + old_article["similarity_score"] < 20:
        pruned += 1
        continue

    title = old_article.get("title") or ""
    description = old_article.get("description") or ""

    old_article["entities"] = extract_entities_gliner(title + " " + description)
    old_article["themes"] = detect_themes_zeroshot(title + " " + description)

    new_graph_handler.add_article_node(old_article["_id"], old_article, old_article["embedding"],
                                       old_article["entities"], old_article["themes"])

    old_article["graph_score"] = new_graph_handler.graph_score(old_article["_id"])

    if old_article["graph_score"] + old_article["similarity_score"] + old_article["interest_score"] < 30:
        continue

    old_article["final_score"] = old_article["graph_score"] + old_article["similarity_score"] + old_article[
        "interest_score"]
    add_to_new.append(old_article)

new_articles_db.bulk_add_articles(add_to_new)

print("pruned:", pruned)
