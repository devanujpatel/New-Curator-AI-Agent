from difflib import get_close_matches
import re


def _normalize_text(self, text: str) -> str:
    """Normalize text for comparison"""
    return re.sub(r'[^\w\s]', '', text.lower().strip())


def normalize_and_match_2(names_list, input_str, cutoff=0.50):
    # todo: have manual mappings for eg president trump and trump -> trump

    """
    Check if input_str exists in names_list, handle fuzzy matches,
    or append if new.

    Args:
        names_list (list[str]): List of existing names.
        input_str (str): New candidate string.
        cutoff (float): Similarity threshold (0–1).

    Returns:
        str: The matched or added string.
    """
    # Normalize inputs (case-insensitive, stripped)
    input_norm = input_str.strip().lower()
    normalized_list = [n.strip().lower() for n in names_list]

    # Case 1: exact match
    if input_norm in normalized_list:
        return names_list[normalized_list.index(input_norm)]

    # todo: can add bonus for same type

    # Case 2: fuzzy close match
    matches = get_close_matches(input_norm, normalized_list, n=1, cutoff=cutoff)
    if matches:
        return names_list[normalized_list.index(matches[0])]

    # Case 3: new string
    names_list.append(input_str)
    return input_str

#
# names = ["chip stocks", "AI stocks", "Trump"]
#
# print(normalize_and_match_2(names, "ai stocks"))        # → "AI stocks"
# print(normalize_and_match_2(names, "president trump"))  # → "Trump"
# print(normalize_and_match_2(names, "cloud computing"))  # → "cloud computing"
# print(normalize_and_match_2(names, "high power computing"))  # → "cloud computing"
# print(normalize_and_match_2(names, "prime minister"))  # → "cloud computing"
# print(normalize_and_match_2(names, "pharmacy stocks"))  # → "cloud computing"
# print(normalize_and_match_2(names, "president"))  # → "cloud computing"
# print(names)
# # ["chip stocks", "AI stocks", "Trump", "cloud computing"]

# Entity matching thresholds
# ENTITY_SIMILARITY_THRESHOLD = 0.85
#
# for record in results:
#     existing_normalized = record["normalized_name"]
#     existing_name = record["name"]
#     existing_type = record["type"]
#
#     # Type matching bonus if both have types
#     type_bonus = 0.1 if (entity_type and existing_type and
#                          entity_type.lower() == existing_type.lower()) else 0
#
#     # Calculate similarity
#     similarity = SequenceMatcher(None, normalized_name, existing_normalized).ratio()
#     similarity += type_bonus
#
#     if similarity > best_similarity and similarity >= ENTITY_SIMILARITY_THRESHOLD:
#         best_similarity = similarity
#         best_match = (record["id"], existing_name)
#
# return best_match if best_match else (None, None)
