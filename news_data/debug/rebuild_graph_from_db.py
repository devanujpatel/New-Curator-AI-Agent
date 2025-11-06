from networkx.readwrite import json_graph
import json
import networkx as nx
import numpy as np
from itertools import combinations
from ranker.graph_handler import GraphHandler
from news_data.db.articles import ArticleDB
from news_data.db.database import Database
from news_data.helper.get_cosine_similarity import cosine_similarity

SIMILARITY_THRESHOLD = 0.5
GRAPH_PATH = "../graph_data/new_graph_0_05.json"

def build_article_graph(similarity_threshold=SIMILARITY_THRESHOLD):
    # Connect to MongoDB
    db = Database()
    articles_db = ArticleDB(db)

    # Load all articles
    articles = articles_db.get_all_articles()  # list of dicts

    # Create NetworkX graph
    G = nx.Graph()

    # Add nodes with metadata
    for article in articles:
        G.add_node(
            str(article["_id"]),          # use MongoDB _id as node ID
            title=article.get("title", ""),
            description=article.get("description", ""),
            feedback=article.get("feedback", ""),
            note=article.get("note", ""),
            embedding=np.array(article.get("embedding", []), dtype=np.float32)
        )

    # Compare all pairs for similarity
    for a1, a2 in combinations(articles, 2):
        emb1 = np.array(a1.get("embedding", []), dtype=np.float32)
        emb2 = np.array(a2.get("embedding", []), dtype=np.float32)
        sim = cosine_similarity(emb1, emb2)
        if sim > similarity_threshold:
            G.add_edge(str(a1["_id"]), str(a2["_id"]), weight=sim)

    # Save as JSON
    data = json_graph.node_link_data(G, edges="edges")

    # Convert numpy arrays to lists for JSON
    for node in data["nodes"]:
        if isinstance(node.get("embedding"), np.ndarray):
            node["embedding"] = node["embedding"].tolist()

    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)

    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Graph built with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# Example usage
if __name__ == "__main__":
    build_article_graph()
