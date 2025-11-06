from sentence_transformers import util

def similar_article_score(article_embedding, liked_embeddings):
    """
    article_embedding: torch.Tensor
    liked_embeddings: list of torch.Tensor (from FAISS or DB)
    Returns average of mean and max similarity.
    """
    if not liked_embeddings:
        print("no liked embeddings")
        return 0.0

    sims = [util.pytorch_cos_sim(article_embedding, le).item() for le in liked_embeddings]
    mean_sim = sum(sims) / len(sims)
    max_sim = max(sims)

    # average of mean and max similarity
    score = (mean_sim + max_sim) / 2

    # scale to 0-100
    return score * 100
