import networkx as nx
from networkx.readwrite import json_graph
import numpy as np
import json
import os
from news_data.helper.get_cosine_similarity import cosine_similarity

SIMILARITY_THRESHOLD = 0.05
LOVE_WEIGHT = 1.0
LIKE_WEIGHT = 0.5
DISLIKE_WEIGHT = -0.25


class GraphHandler:
    def __init__(self, graph_path="graph_data/new_graph_0_05.json"):  # all_articles_graph.json"):
        self.graph_path = graph_path
        if os.path.exists(self.graph_path):
            self.graph = self._load()
        else:
            self.graph = nx.Graph()

    def save(self):
        os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
        data = json_graph.node_link_data(self.graph, edges="edges")

        # Convert numpy arrays to lists for JSON
        for node in data["nodes"]:
            if isinstance(node.get("embedding"), np.ndarray):
                node["embedding"] = node["embedding"].tolist()

        with open(self.graph_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        with open(self.graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert embeddings back to numpy arrays
        for node in data["nodes"]:
            if "embedding" in node and isinstance(node["embedding"], list):
                node["embedding"] = np.array(node["embedding"], dtype=np.float32)

        return json_graph.node_link_graph(data, edges="edges")

    # -------------------
    # Node Management
    # -------------------
    def add_article_node(self, article_id, metadata, embedding):
        """
        article_id: MongoDB _id (ObjectId or str)
        metadata: other fields like url, title, feedback, etc.
        embedding: numpy array or list
        """
        embedding_np = np.array(embedding, dtype=np.float32)

        # Ensure article_id is string for consistency in NetworkX
        node_id = str(article_id)

        self.graph.add_node(
            node_id,
            **metadata,
            embedding=embedding_np,
            feedback=metadata.get("feedback", "skipped")
        )

        # Compare to existing nodes to create edges
        for other_id, data in self.graph.nodes(data=True):
            if other_id == node_id:
                continue
            sim = cosine_similarity(embedding_np, data["embedding"])
            if sim >= SIMILARITY_THRESHOLD:
                self.graph.add_edge(node_id, other_id, weight=sim)

        self.save()

    def update_feedback(self, article_id, feedback):
        node_id = str(article_id)
        if node_id not in self.graph:
            return
        self.graph.nodes[node_id]["feedback"] = feedback
        self.save()

    def delete_today_nodes(self, article_ids):
        # Convert all MongoDB ObjectIds to strings for NetworkX
        node_ids = [str(aid) for aid in article_ids]
        self.graph.remove_nodes_from(node_ids)
        self.save()

    # -------------------
    # Scoring
    # -------------------
    # def graph_score(self, article_id):
    #     neighbour_score = self.neighbour_weight_feedback_score(article_id)
    #     closeness_score = self.get_closeness_centrality_score(article_id)
    #     return 0.4*neighbour_score + 0.6*closeness_score

    def graph_score(self, article_id):
        """
        Calculate a score based on similarities to loved, liked, or disliked articles.
        Positive edges get weighted more heavily, negative edges penalize lightly.
        """
        if article_id not in self.graph:
            print("no article node")
            return 0.0

        edges = self.graph.edges(article_id, data=True)
        if not edges:
            print("no edges for article")
            return 0.0

        weighted_scores = []
        for _, neighbor_id, d in edges:
            weight = d["weight"]
            feedback = self.graph.nodes[neighbor_id].get("feedback", "skipped")

            if feedback == "love":
                weighted_scores.append(weight * LOVE_WEIGHT)
            elif feedback == "like":
                weighted_scores.append(weight * LIKE_WEIGHT)
            elif feedback == "dislike":
                weighted_scores.append(weight * DISLIKE_WEIGHT)
            # skipped or no feedback → no contribution

        if not weighted_scores:
            print("no weighted scores")
            return 0.0

        # Mean of weighted scores
        mean_score = float(np.mean(weighted_scores))

        # Scale to -25 → 100
        scaled_score = mean_score * 100

        return scaled_score

    # def get_closeness_to_liked(self, article_id):
    #     # Get the subset of liked/loved nodes
    #     liked_nodes = [
    #         n for n, data in self.graph.nodes(data=True)
    #         if data.get("feedback") in {"like", "love"} and n != article_id
    #     ]
    #     if not liked_nodes:
    #         print("no liked nodes")
    #         return 0  # No liked nodes to measure closeness against
    #
    #     # Compute shortest path lengths from the given article to each liked node
    #     lengths = nx.single_source_dijkstra_path_length(self.graph, article_id, weight='weight')
    #
    #     # Only keep distances to liked nodes
    #     distances = [lengths[n] for n in liked_nodes if n in lengths]
    #
    #     if not distances:
    #         print("no liked nodes reachable")
    #         return 0  # No reachable liked nodes
    #
    #     # Closeness centrality restricted to liked nodes
    #     return len(distances) / sum(distances)
