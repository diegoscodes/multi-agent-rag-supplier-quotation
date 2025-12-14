
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """
    Wrapper around SentenceTransformer to generate embeddings.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str):
        """
        Returns the embedding vector for a single text string.
        """
        return self.model.encode(text)
