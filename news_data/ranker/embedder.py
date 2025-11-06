from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def get_text_embedding(self, text):
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def get_article_embedding(self, article):
        title = article.get("title") or ""  # fallback to empty string
        description = article.get("description") or ""  # fallback to empty string
        notes = article.get("notes") or ""
        text = f"{title} {description} {notes}".strip()

        return self.get_text_embedding(text)