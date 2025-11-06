from neo4j import GraphDatabase
import json

# Neo4j connection details
URI = "neo4j://127.0.0.1:7687"  # Update if needed
USER = "neo4j"
PASSWORD = "ADD PWD HERE"
# or figure out way to store in ENV

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def fix_embeddings(tx):
    # Get ALL nodes and their properties
    query_all = """
    MATCH (n)
    RETURN id(n) AS node_id, n AS node
    """
    results = tx.run(query_all)

    for record in results:
        node_id = record["node_id"]
        node_props = dict(record["node"])

        # Skip nodes without 'embedding'
        if "embedding" not in node_props:
            continue

        embedding = node_props["embedding"]

        # If it's a string, convert and update
        if isinstance(embedding, str):
            try:
                arr = json.loads(embedding)  # Convert to Python list
                if isinstance(arr, list):
                    arr = [float(x) for x in arr]  # Ensure floats
                    tx.run(
                        """
                        MATCH (n) WHERE id(n) = $node_id
                        SET n.embedding = $arr
                        """,
                        node_id=node_id,
                        arr=arr
                    )
                    print(f"Fixed embedding for node {node_id}")
            except Exception as e:
                print(f"Error parsing node {node_id}: {e}")


with driver.session(database='aura-vectors-db') as session:
    session.execute_write(fix_embeddings)

driver.close()
