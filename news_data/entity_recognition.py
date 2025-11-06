import pickle
import os
from typing import List, Tuple

from gliner import GLiNER
from sentence_transformers import util
from news_data.ranker.embedder import EmbeddingService

# Load pretrained GLiNER model
gliner_model = GLiNER.from_pretrained("urchade/gliner_base")

# Define label set (can be extended)
labels = ["Person", "Company", "Country", "Organization"]

# load lightweight embedding model once (CPU-friendly, ~100MB RAM)
embedder = EmbeddingService().model

# configurable thresholds
CONF_THRESHOLD = 0.55
SIM_THRESHOLD = 0.65
ENTITY_STORE = "entity_label_list.pkl"

# preload existing entities
if os.path.exists(ENTITY_STORE):
    with open(ENTITY_STORE, "rb") as f:
        existing_entities = pickle.load(f)
else:
    existing_entities = []


def extract_entities_gliner(text: str) -> List[Tuple[str, str, float]]:
    """
    Extract + normalize entities from text using GLiNER.
    Returns list of (entity_text, label, confidence).
    """
    raw_entities = gliner_model.predict_entities(text, labels=labels)

    # Step 1: filter low confidence
    entities = [
        (e["text"].strip(), e["label"], round(e["score"], 2))
        for e in raw_entities
        if e["score"] >= CONF_THRESHOLD
    ]

    if not entities:
        return []

    # Step 2: merge duplicates (semantic + literal)
    entities = merge_duplicates_semantic(entities, SIM_THRESHOLD)

    # Step 3: normalize against existing entity store
    for idx, (entity_name, label, conf) in enumerate(entities):
        normalized = normalize_and_match(existing_entities, entity_name)
        entities[idx] = (normalized, label, conf)

        if normalized not in existing_entities:
            existing_entities.append(normalized)

    # Step 4: persist updated entity list
    with open(ENTITY_STORE, "wb") as f:
        pickle.dump(existing_entities, f)

    return entities


def merge_duplicates_semantic(entities, threshold=0.65):
    """
    Merge duplicates using semantic similarity (embeddings).
    Keeps the longest/highest-confidence entity per group.
    """
    if len(entities) == 1:
        return entities

    texts = [e[0] for e in entities]
    embeddings = embedder.encode(texts, convert_to_tensor=True, show_progress_bar=False)

    # cosine similarity matrix
    sim_matrix = util.cos_sim(embeddings, embeddings).cpu().numpy()

    clustered = []
    used = set()

    for i in range(len(entities)):
        if i in used:
            continue

        group = [entities[i]]
        used.add(i)

        for j in range(i + 1, len(entities)):
            if j in used:
                continue
            if (
                    entities[i][1] == entities[j][1]  # same label
                    and sim_matrix[i][j] >= threshold
            ):
                group.append(entities[j])
                used.add(j)

        # pick representative: longest text, break ties by confidence
        rep = max(group, key=lambda x: (len(x[0]), x[2]))
        clustered.append(rep)

    return clustered


def normalize_and_match(existing: List[str], new_entity: str) -> str:
    """
    Normalize new entity by matching against existing ones using semantic similarity.
    Returns best existing match if above threshold, else the original.
    """
    if not existing:
        return new_entity

    embeddings_existing = embedder.encode(existing, convert_to_tensor=True, show_progress_bar=False)
    embedding_new = embedder.encode(new_entity, convert_to_tensor=True, show_progress_bar=False)

    sims = util.cos_sim(embedding_new, embeddings_existing).cpu().numpy()[0]
    best_idx = sims.argmax()
    best_score = sims[best_idx]

    if best_score >= 0.75:  # stricter for existing matches
        return existing[best_idx]
    return new_entity


print(extract_entities_gliner(
    "Tesla announces record Q2 earnings amid growing competition in China. Tesla Inc. reported a 25% increase in quarterly revenue, driven by strong demand for the Model Y and expanding operations in Shanghai. CEO Elon Musk highlighted plans for a new gigafactory in India, while analysts warned of rising competition from BYD and NIO. The company’s stock ticker (TSLA) surged 7% in after-hours trading following the announcement of the earnings report."))

"""import pickle

from gliner import GLiNER
import difflib

from news_data.helper.similar_in_list_checker import normalize_and_match_2

# Load pretrained GLiNER model
gliner_model = GLiNER.from_pretrained("urchade/gliner_base")

# Define label set (can be extended)
labels = ["Person", "Company", "Country", "Organization"]

existing_labels = []
with open(r"C:\DEV\coding\MSN\news_data\entity_label_list_2.pkl", "rb") as f:
    existing_entities = pickle.load(f)


def extract_entities_gliner(text: str):
    """
# Extract entities using GLiNER with custom labels.
# Returns list of (entity_text, label).
"""
entities = gliner_model.predict_entities(text, labels=labels)
# todo: can add threshold for entity confidence
entities = merge_duplicates([(ent["text"], ent["label"], round(ent["score"], 2)) for ent in entities])

for idx, (entity_name, _, _) in enumerate(entities):
    to_keep = normalize_and_match_2(existing_entities, entity_name)
    entities[idx][0] = to_keep

with open("entity_label_list.pkl", "wb") as f:
    pickle.dump(existing_entities, f)

return entities


def merge_duplicates(entities, similarity_threshold=0.6):
"""
# Merge literal and loose duplicates in NER outputs.
#
# Args:
#     entities (list of tuples): [(text, label), ...]
#     similarity_threshold (float): similarity ratio (0–1) for loose match.
#
# Returns:
#     list of tuples: deduplicated + merged entities
"""
# Step 1: remove literal duplicates (use a set)
unique_entities = []
seen = set()
for ent in entities:
    if ent not in seen:
        unique_entities.append(ent)
        seen.add(ent)

# Step 2: handle loose duplicates
merged = []
skip = set()
n = len(unique_entities)

for i in range(n):
    if i in skip:
        continue
    text1, label1, conf1 = unique_entities[i]
    best = [text1, label1, conf1]

    for j in range(i + 1, n):
        if j in skip:
            continue
        text2, label2, conf2 = unique_entities[j]

        if label1 == label2:
            sim = difflib.SequenceMatcher(None, text1, text2).ratio()
            if sim >= similarity_threshold:
                # pick longer text as "better" entity
                best = max([best, [text2, label2, conf2]], key=lambda x: len(x[0]))
                skip.add(j)

    merged.append(best)

return merged

# db = Database()
# articles_db = ArticleDB(db)
#
# articles = articles_db.get_all_articles()
# for article in articles:
#     if "final_score" in article and article["final_score"] > 0.60:
#         title = article.get("title") or ""
#         description = article.get("description") or ""
#
#         entities = extract_entities_gliner(title + " " + description)
#         print(f"{title+description}: \n\t{entities}\n")


# import pickle
#
# # Create an empty Python list
# my_empty_list = []
#
# # Define the filename for the pickle file
# filename = 'entity_label_list_2.pkl'
#
# # Open the file in binary write mode and dump the empty list
# try:
#     with open(filename, 'wb') as f:
#         pickle.dump(my_empty_list, f)
#     print(f"Blank pickle file '{filename}' with an empty list created successfully.")
# except Exception as e:
#     print(f"An error occurred: {e}")
"""
