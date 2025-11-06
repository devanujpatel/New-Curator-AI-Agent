from sentence_transformers import SentenceTransformer, util

interest_text = "I am interested in AI, stock market, Apple, Tesla, and inflation."

# Load model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
interest_embedding = model.encode(interest_text, convert_to_tensor=True)


def score_articles_with_embeddings(articles):
    """
    Scores each article based on semantic similarity with the user's interests.

    Args:
        articles (list[dict]): List of articles with 'title' and optionally 'description'.
        interest_text (str): A string describing the user's interests.

    Returns:
        list[dict]: Articles with an added 'score' key.
    """

    interest_embedding = model.encode(interest_text, convert_to_tensor=True)

    for article in articles:
        title = article.get("title") or ""  # fallback to empty string
        description = article.get("description") or ""  # fallback to empty string
        text = f"{title} {description}"

        article_embedding = model.encode(text, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(interest_embedding, article_embedding).item()
        article["score"] = similarity

    # Return articles sorted by score (highest first)
    return articles


def single_article_scorer(article):
    title = article.get("title") or ""  # fallback to empty string
    description = article.get("description") or ""  # fallback to empty string
    text = f"{title} {description}"

    article_embedding = model.encode(text, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(interest_embedding, article_embedding).item()

    return similarity, article_embedding