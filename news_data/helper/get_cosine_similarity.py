import numpy as np


def cosine_similarity(vec1, vec2):
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: list or np.ndarray
        vec2: list or np.ndarray

    Returns:
        float: cosine similarity between -1 and 1
    """
    # Convert to numpy arrays
    v1 = np.array(vec1, dtype=np.float32)
    v2 = np.array(vec2, dtype=np.float32)

    # Handle zero vectors
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0

    # Cosine similarity formula
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
