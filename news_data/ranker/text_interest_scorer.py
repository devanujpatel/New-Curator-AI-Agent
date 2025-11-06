from news_data.helper.get_cosine_similarity import cosine_similarity
from news_data.ranker import embedder

embedder = embedder.EmbeddingService()

user_interest_statement = "I’m interested in AI, the U.S. stock market, the global economy, investment strategies, and emerging technologies."
interest_embedding = embedder.get_text_embedding(user_interest_statement)

def text_interest_score(article_embedding):
    return cosine_similarity(article_embedding, interest_embedding) * 100

