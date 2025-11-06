from sentence_transformers import util
from news_data.feedback.feedback_manager import load_feedback_embeddings
from news_data.ranker.embedding_scorer import single_article_scorer


def compute_feedback_score(article_embedding, liked_embeddings, disliked_embeddings):
    """
    Compute feedback-based score for an article using:
      - Mean similarity to liked/disliked articles
      - Max similarity to liked/disliked articles
    Each contributes 50% within the allocated weight.
    """
    score = 0.0

    # --- Handle Liked/Loved Articles ---
    if liked_embeddings:
        sims = [util.pytorch_cos_sim(article_embedding, emb).item()
                for emb in liked_embeddings]
        mean_sim = sum(sims) / len(sims)
        max_sim = max(sims)

        # 0.4 total weight -> 0.2 mean + 0.2 max
        score += 0.2 * mean_sim + 0.2 * max_sim

    # --- Handle Disliked Articles ---
    if disliked_embeddings:
        sims = [util.pytorch_cos_sim(article_embedding, emb).item()
                for emb in disliked_embeddings]
        mean_sim = sum(sims) / len(sims)
        max_sim = max(sims)

        # 0.3 total weight -> 0.15 mean + 0.15 max (subtract because it's a penalty)
        score -= 0.15 * mean_sim + 0.15 * max_sim

    return score


def compute_final_score(base_score, article_embedding, liked_embeddings, disliked_embeddings):
    """
    Combine base content-based score and feedback similarity.
    """
    feedback_score = compute_feedback_score(article_embedding, liked_embeddings, disliked_embeddings)
    return 0.6 * base_score + 0.4 * feedback_score


def rank_articles(articles, embedding_model):
    """
    Rank articles based on base score + feedback score.

    Articles must have:
        - "title"
        - "score" (base score from your content-based filter)
    """
    liked_embeddings, disliked_embeddings = load_feedback_embeddings()

    for article in articles:
        # Compute embedding for personalized scoring
        score, embedding = single_article_scorer(article)

        article["final_score"] = compute_final_score(
            base_score=score,
            article_embedding=embedding,
            liked_embeddings=liked_embeddings,
            disliked_embeddings=disliked_embeddings
        )

    # Sort and return top articles
    return sorted(articles, key=lambda x: x["final_score"], reverse=True)
