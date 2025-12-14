import chromadb
from chromadb.config import Settings


class VectorStore:
    def __init__(self, collection_name: str = "offers"):
        self.collection_name = collection_name
        self.client = chromadb.Client(
            Settings(
                persist_directory=".chroma",
                anonymized_telemetry=False,
            )
        )
        self._init_collection()

    def _init_collection(self):
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

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
        self.client.delete_collection(self.collection_name)
        self._init_collection()
