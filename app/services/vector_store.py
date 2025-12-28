import os
import chromadb
from chromadb.config import Settings


class VectorStore:
    def __init__(self, collection_name: str = "offers", persist_directory: str | None = ".chroma"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        settings = Settings(anonymized_telemetry=False)

        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory, settings=settings)
        else:
            # In-memory (great for tests)
            self.client = chromadb.Client(settings)

        self._init_collection()

    def _init_collection(self):
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_document(self, doc_id: str, text: str, embedding, metadata: dict):
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def query(self, query_embedding, n_results: int = 5):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

    def reset(self):
        # Safe reset for tests / dev
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._init_collection()
