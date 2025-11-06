from neo4j import GraphDatabase
import numpy as np
from news_data.helper.get_cosine_similarity import cosine_similarity
from difflib import SequenceMatcher
import re

SIMILARITY_THRESHOLD = 0.50
LOVE_WEIGHT = 1.0
LIKE_WEIGHT = 0.5
DISLIKE_WEIGHT = -0.25


class Neo4jGraphHandler:
    def __init__(self, uri: str, user: str, password: str, db_name: str = "aura-vectors-db"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.db_name = db_name
        # self._create_indexes()

    def close(self):
        self.driver.close()

    def _create_or_get_entity(self, entity_name: str, entity_type: str = None):
        """Create a new entity if it doesn't exist, otherwise update existing"""

        query = """
        MERGE (e:Entity {name: $name})
        ON CREATE SET
            e.name = $name,
            e.type = $type,
            e.mention_count = 1,
            e.created_at = datetime()
        ON MATCH SET
            e.type = COALESCE($type, e.type),
            e.mention_count = e.mention_count + 1
        RETURN e.name AS name
        """

        with self.driver.session(database=self.db_name) as session:
            result = session.run(query, {
                "name": entity_name,
                "type": entity_type,
            })
            record = result.single()
            return record["name"]

    def _create_or_get_theme(self, theme_name, theme_score):
        """Create a new theme if it doesn't exist, otherwise update existing"""

        query = """
        MERGE (t:Theme {name: $name})
        ON CREATE SET
            t.name = $name,
            t.mention_count = 1,
            t.score = $score,
            t.created_at = datetime()
        ON MATCH SET
            t.mention_count = t.mention_count + 1
        RETURN t.name AS name
        """

        with self.driver.session(database=self.db_name) as session:
            result = session.run(query, {
                "name": theme_name,
                "score": theme_score,
            })
            record = result.single()
            return record["name"]

    # -------------------
    # Node Management
    # -------------------
    def add_article_node(self, article_id, metadata: dict, embedding, entities: list = None, themes: list = None):
        """
        article_id: MongoDB _id (ObjectId or str)
        metadata: dict containing url, title, reaction, note, etc.
        embedding: numpy array or list
        entities: list of dicts with keys: name, type (optional), description (optional)
        themes: list of dicts with keys: name, description (optional)
        """
        node_id = str(article_id)
        embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        entities = entities or []
        themes = themes or []

        with self.driver.session(database=self.db_name) as session:
            # Create article node with native embedding array
            session.run(
                """
                MERGE (a:Article {id: $id})
                SET a.title = $title,
                    a.url = $url,
                    a.description = $description,
                    a.category = $category,
                    a.reaction = COALESCE($reaction, 'skipped'),
                    a.note = COALESCE($note, 'skipped'),
                    a.embedding = $embedding,
                    a.updated_at = datetime()
                """,
                {
                    "id": node_id,
                    "title": metadata.get("title", ""),
                    "url": metadata.get("url", ""),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", ""),
                    "reaction": metadata.get("reaction"),
                    "note": metadata.get("note"),
                    "embedding": embedding_list
                },
            )

            # Process and connect entities
            for entity_data in entities:
                entity_name = entity_data[0].strip()
                if not entity_name:
                    continue

                entity_type = entity_data[1]

                # Create or get existing entity
                self._create_or_get_entity(entity_name, entity_type)

                # Create relationship between article and entity
                session.run("""
                    MATCH (a:Article {id: $article_id}), (e:Entity {name: $entity_name})
                    MERGE (a)-[r:MENTIONS_ENTITY]->(e)
                    SET r.original_mention = $original_mention,
                        r.created_at = datetime(),
                        r.score = $score
                """, {
                    "article_id": node_id,
                    "entity_name": entity_name,
                    "original_mention": entity_name,
                    "score": int(entity_data[2])
                })

            # Process and connect themes
            for theme_data in themes:
                theme_name = theme_data[0].strip()
                if not theme_name:
                    continue

                # Create or get existing theme
                self._create_or_get_theme(theme_name, theme_data[1])

                # Create relationship between article and theme
                session.run("""
                    MATCH (a:Article {id: $article_id}), (t:Theme {name: $theme_name})
                    MERGE (a)-[r:HAS_THEME]->(t)
                    SET r.created_at = datetime(),
                    r.score = $score
                """, {
                    "article_id": node_id,
                    "theme_name": theme_name,
                    "score": int(theme_data[1])
                })

            # Create similarity edges with other articles (existing logic)
            neighbors = session.run(
                """
                MATCH (other:Article)
                WHERE other.id <> $id AND other.embedding IS NOT NULL
                RETURN other.id AS other_id, other.embedding AS embedding
                """,
                {"id": node_id},
            )

            for record in neighbors:
                other_id = record["other_id"]
                other_embedding = record["embedding"] or []
                if other_embedding:  # Make sure embedding exists
                    sim = cosine_similarity(np.array(embedding_list), np.array(other_embedding))
                    if sim >= SIMILARITY_THRESHOLD:
                        session.run(
                            """
                            MATCH (a:Article {id: $id}), (b:Article {id: $other_id})
                            MERGE (a)-[r:SIMILAR_TO]->(b)
                            SET r.weight = $weight,
                                r.updated_at = datetime()
                            """,
                            {"id": node_id, "other_id": other_id, "weight": sim},
                        )

    def update_reaction(self, article_id, reaction):
        node_id = str(article_id)
        with self.driver.session(database=self.db_name) as session:
            session.run(
                """
                MATCH (a:Article {id: $id}) 
                SET a.reaction = $reaction, a.updated_at = datetime()
                """,
                {"id": node_id, "reaction": reaction},
            )

    def delete_today_nodes(self, article_ids):
        node_ids = [str(aid) for aid in article_ids]
        with self.driver.session(database=self.db_name) as session:
            # Delete articles and their relationships
            session.run(
                """
                MATCH (a:Article)
                WHERE a.id IN $ids
                DETACH DELETE a
                """,
                {"ids": node_ids},
            )

            # Clean up orphaned entities and themes (optional)
            session.run("""
                MATCH (e:Entity)
                WHERE NOT (e)<-[:MENTIONS_ENTITY]-(:Article)
                DELETE e
            """)

            session.run("""
                MATCH (t:Theme)
                WHERE NOT (t)<-[:HAS_THEME]-(:Article)
                DELETE t
            """)

    # -------------------
    # Enhanced Scoring
    # -------------------
    def graph_score(self, article_id):
        """Enhanced scoring including entity and theme connections"""
        node_id = str(article_id)
        with self.driver.session(database=self.db_name) as session:
            # Original similarity-based scoring
            similarity_result = session.run(
                """
                MATCH (a:Article {id: $id})-[r:SIMILAR_TO]->(neighbor:Article)
                RETURN neighbor.reaction AS reaction, r.weight AS weight
                """,
                {"id": node_id},
            )

            weighted_scores = []
            for record in similarity_result:
                weight = record["weight"]
                reaction = record["reaction"] or "skipped"
                if reaction == "love":
                    weighted_scores.append(weight * LOVE_WEIGHT)
                elif reaction == "like":
                    weighted_scores.append(weight * LIKE_WEIGHT)
                elif reaction == "dislike":
                    weighted_scores.append(weight * DISLIKE_WEIGHT)

            similarity_score = float(np.mean(weighted_scores)) if weighted_scores else 0.0

            # Entity-based scoring
            entity_result = session.run("""
                MATCH (a:Article {id: $id})-[:MENTIONS_ENTITY]->(e:Entity)<-[:MENTIONS_ENTITY]-(other:Article)
                WHERE other.id <> $id AND other.reaction IS NOT NULL AND other.reaction <> 'skipped'
                RETURN other.reaction AS reaction, count(*) AS shared_entities
            """, {"id": node_id})

            entity_scores = []
            for record in entity_result:
                reaction = record["reaction"]
                shared_count = record["shared_entities"]
                entity_weight = min(shared_count * 0.1, 0.5)  # Cap at 0.5

                if reaction == "love":
                    entity_scores.append(entity_weight * LOVE_WEIGHT)
                elif reaction == "like":
                    entity_scores.append(entity_weight * LIKE_WEIGHT)
                elif reaction == "dislike":
                    entity_scores.append(entity_weight * DISLIKE_WEIGHT)

            entity_score = float(np.mean(entity_scores)) if entity_scores else 0.0

            # Theme-based scoring
            theme_result = session.run("""
                MATCH (a:Article {id: $id})-[:HAS_THEME]->(t:Theme)<-[:HAS_THEME]-(other:Article)
                WHERE other.id <> $id AND other.reaction IS NOT NULL AND other.reaction <> 'skipped'
                RETURN other.reaction AS reaction, count(*) AS shared_themes
            """, {"id": node_id})

            theme_scores = []
            for record in theme_result:
                reaction = record["reaction"]
                shared_count = record["shared_themes"]
                theme_weight = min(shared_count * 0.15, 0.6)  # Cap at 0.6

                if reaction == "love":
                    theme_scores.append(theme_weight * LOVE_WEIGHT)
                elif reaction == "like":
                    theme_scores.append(theme_weight * LIKE_WEIGHT)
                elif reaction == "dislike":
                    theme_scores.append(theme_weight * DISLIKE_WEIGHT)

            theme_score = float(np.mean(theme_scores)) if theme_scores else 0.0

            # Combined scoring with weights
            final_score = (similarity_score * 0.5) + (entity_score * 0.3) + (theme_score * 0.2)
            scaled_score = final_score * 100

            return scaled_score

    # -------------------
    # Query Methods
    # -------------------
    def get_article_entities_and_themes(self, article_id):
        """Get entities and themes for an article"""
        node_id = str(article_id)
        with self.driver.session(database=self.db_name) as session:
            result = session.run("""
                MATCH (a:Article {id: $id})
                OPTIONAL MATCH (a)-[:MENTIONS_ENTITY]->(e:Entity)
                OPTIONAL MATCH (a)-[:HAS_THEME]->(t:Theme)
                RETURN 
                    collect(DISTINCT {name: e.name, type: e.type}) AS entities,
                    collect(DISTINCT {name: t.name}) AS themes
            """, {"id": node_id})

            record = result.single()
            if record:
                return {
                    "entities": [e for e in record["entities"] if e["name"]],
                    "themes": [t for t in record["themes"] if t["name"]]
                }
            return {"entities": [], "themes": []}

    def find_articles_by_entity(self, entity_name: str, limit: int = 10):
        """Find articles that mention a specific entity"""
        with self.driver.session(database=self.db_name) as session:
            result = session.run("""
                MATCH (e:Entity)-[:MENTIONS_ENTITY]-(a:Article)
                WHERE e.name CONTAINS $name
                RETURN a.id AS article_id, a.title AS title, e.name AS entity_name
                ORDER BY a.updated_at DESC
                LIMIT $limit
            """, {
                "entity_name": entity_name,
                "limit": limit
            })

            return [{"article_id": r["article_id"], "title": r["title"],
                     "entity_name": r["entity_name"]} for r in result]

    def find_articles_by_theme(self, theme_name: str, limit: int = 10):
        """Find articles that have a specific theme"""
        with self.driver.session(database=self.db_name) as session:
            result = session.run("""
                MATCH (t:Theme)-[:HAS_THEME]-(a:Article)
                WHERE t.name CONTAINS $theme_name
                RETURN a.id AS article_id, a.title AS title, t.name AS theme_name
                ORDER BY a.updated_at DESC
                LIMIT $limit
            """, {
                "theme_name": theme_name,
                "limit": limit
            })

            return [{"article_id": r["article_id"], "title": r["title"],
                     "theme_name": r["theme_name"]} for r in result]

    def get_popular_entities_and_themes(self, limit: int = 20):
        """Get most mentioned entities and themes"""
        with self.driver.session(database=self.db_name) as session:
            entities_result = session.run("""
                MATCH (e:Entity)
                RETURN e.name AS name, e.mention_count AS count, e.type AS type
                ORDER BY e.mention_count DESC
                LIMIT $limit
            """, {"limit": limit})

            themes_result = session.run("""
                MATCH (t:Theme)
                RETURN t.name AS name, t.mention_count AS count
                ORDER BY t.mention_count DESC
                LIMIT $limit
            """, {"limit": limit})

            return {
                "entities": [{"name": r["name"], "count": r["count"], "type": r["type"]}
                             for r in entities_result],
                "themes": [{"name": r["name"], "count": r["count"]}
                           for r in themes_result]
            }

    # -------------------
    # Neo4j vector similarity query (enhanced)
    # -------------------
    def top_k_similar(self, embedding, k=5, include_entities_themes=False):
        """
        Returns top-k articles most similar to given embedding using cosine similarity.
        Optionally include entities and themes.
        """
        embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        with self.driver.session(database=self.db_name) as session:
            base_query = """
            MATCH (a:Article)
            WHERE a.embedding IS NOT NULL
            """

            if include_entities_themes:
                query = base_query + """
                OPTIONAL MATCH (a)-[:MENTIONS_ENTITY]->(e:Entity)
                OPTIONAL MATCH (a)-[:HAS_THEME]->(t:Theme)
                RETURN a.id AS id, a.title AS title, 
                       gds.similarity.cosine(a.embedding, $embedding) AS sim,
                       collect(DISTINCT e.name) AS entities,
                       collect(DISTINCT t.name) AS themes
                ORDER BY sim DESC
                LIMIT $k
                """
                result = session.run(query, {"embedding": embedding_list, "k": k})
                return [{
                    "id": r["id"],
                    "title": r["title"],
                    "similarity": r["sim"],
                    "entities": [e for e in r["entities"] if e],
                    "themes": [t for t in r["themes"] if t]
                } for r in result]
            else:
                query = base_query + """
                RETURN a.id AS id, a.title AS title, 
                       gds.similarity.cosine(a.embedding, $embedding) AS sim
                ORDER BY sim DESC
                LIMIT $k
                """
                result = session.run(query, {"embedding": embedding_list, "k": k})
                return [{"id": r["id"], "title": r["title"], "similarity": r["sim"]} for r in result]

    # -------------------
    # Advanced Recommendation Methods
    # -------------------

    def find_similar_articles_by_entity(self, article_id, entity_name, limit=20, min_similarity=0.3):
        """
        Find articles that mention the same entity and are similar to the input article
        Uses article_id for efficiency since embedding is already stored
        """
        node_id = str(article_id)

        with self.driver.session(database=self.db_name) as session:
            result = session.run("""
                MATCH (input:Article {id: $article_id})
                MATCH (e:Entity)
                WHERE OR e.name CONTAINS $entity_name
                MATCH (e)<-[:MENTIONS_ENTITY]-(similar:Article)
                WHERE similar.id <> $article_id 
                  AND input.embedding IS NOT NULL 
                  AND similar.embedding IS NOT NULL

                WITH input, similar, e, 
                     gds.similarity.cosine(input.embedding, similar.embedding) AS similarity
                WHERE similarity >= $min_similarity

                RETURN similar.id AS article_id, 
                       similar.title AS title,
                       similar.reaction AS reaction,
                       e.name AS entity_name,
                       similar.description AS description,
                       similar.url as url,
                       similar.note AS note,
                       similar.category AS category,
                       similarity
                ORDER BY similarity DESC
                LIMIT $limit
            """, {
                "article_id": node_id,
                "entity_name": entity_name,
                "min_similarity": min_similarity,
                "limit": limit
            })

            articles_dict = {}
            for r in result:
                articles_dict[r["article_id"]] = {
                    "article_id": r["article_id"],
                    "title": r["title"],
                    "entity_name": r["entity_name"],
                    "similarity": r["similarity"],
                    "reaction": r["reaction"],
                    "description": r["description"],
                    "url": r["url"],
                    "note": r["note"],
                    "category": r["category"]
                }

            return articles_dict

    def find_similar_articles_by_theme(self, article_id, theme_name, limit=10, min_similarity=0.3):
        """
        Find articles that have the same theme and are similar to the input article
        Uses article_id for efficiency since embedding is already stored
        """
        node_id = str(article_id)

        with self.driver.session(database=self.db_name) as session:
            result = session.run("""
                MATCH (input:Article {id: $article_id})
                MATCH (t:Theme)
                WHERE t.name CONTAINS $theme_name
                MATCH (t)<-[:HAS_THEME]-(similar:Article)
                WHERE similar.id <> $article_id 
                  AND input.embedding IS NOT NULL 
                  AND similar.embedding IS NOT NULL

                WITH input, similar, t, 
                     gds.similarity.cosine(input.embedding, similar.embedding) AS similarity
                WHERE similarity >= $min_similarity

                RETURN similar.id AS article_id, 
                       similar.title AS title,
                       similar.reaction AS reaction,
                       t.name AS theme_name,
                       similar.description AS description,
                       similar.url as url,
                       similar.note AS note,
                       similar.category AS category,
                       similarity
                ORDER BY similarity DESC
                LIMIT $limit
            """, {
                "article_id": node_id,
                "theme_name": theme_name,
                "min_similarity": min_similarity,
                "limit": limit
            })

            articles_dict = {}
            for r in result:
                articles_dict[r["article_id"]] = {
                    "article_id": r["article_id"],
                    "title": r["title"],
                    "theme_name": r["theme_name"],
                    "similarity": r["similarity"],
                    "reaction": r["reaction"],
                    "description": r["description"],
                    "url": r["url"],
                    "note": r["note"],
                    "category": r["category"]
                }

            return articles_dict
