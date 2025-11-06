import json
import numpy as np
from neo4j import GraphDatabase
import os

# Path to your NetworkX JSON graph
GRAPH_JSON_PATH = "new_graph_0_05.json"

# Neo4j connection info
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "PWD"#os.environ.get("DB_PWD")
DB_NAME = "aura-vectors-db"

class GraphMigrator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def migrate(self, json_path):
        # Load NetworkX graph
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = data["nodes"]
        edges = data["links"] if "links" in data else data.get("edges", [])

        with self.driver.session(database=DB_NAME) as session:
            # Create nodes
            for node in nodes:
                embedding = node.get("embedding", [])
                # Optionally store as a string if you don't want to use array type
                embedding_str = json.dumps(embedding)
                session.run(
                    """
                    MERGE (a:Article {id: $id})
                    SET a.title = $title,
                        a.url = $url,
                        a.description = $description,
                        a.feedback = $feedback,
                        a.note = $note,
                        a.embedding = $embedding
                    """,
                    {
                        "id": node["id"],
                        "title": node.get("title", ""),
                        "url": node.get("url", ""),
                        "description": node.get("description", ""),
                        "feedback": node.get("feedback", ""),
                        "note": node.get("note", ""),
                        "embedding": embedding_str,
                    },
                )

            # Create edges
            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                weight = edge.get("weight", 0.0)
                session.run(
                    """
                    MATCH (a:Article {id: $source}), (b:Article {id: $target})
                    MERGE (a)-[r:SIMILAR_TO]->(b)
                    SET r.weight = $weight
                    """,
                    {"source": source, "target": target, "weight": weight},
                )


if __name__ == "__main__":
    migrator = GraphMigrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    migrator.migrate(GRAPH_JSON_PATH)
    migrator.close()
    print("Migration complete!")
