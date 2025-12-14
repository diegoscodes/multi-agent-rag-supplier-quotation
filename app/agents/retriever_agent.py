import uuid
from typing import List

from app.models.offer import Offer
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class RetrieverAgent:
    """
    Retrieves relevant supplier offers based on semantic similarity.

    Responsibilities:
    - Generate embeddings for offers at ingestion time
    - Store embeddings and metadata in a vector store
    - Retrieve the most relevant offers for a user query
    """

    def __init__(self):
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore()

    def ingest_offer(self, offer: Offer) -> str:
        """
        Converts an Offer into an embedding and stores it with metadata.
        """
        if not offer.raw_text:
            raise ValueError("Offer raw_text is required for retrieval")

        embedding = self.embedder.embed_text(offer.raw_text)

        metadata = {
            "supplier": offer.supplier or "unknown",
            "item": offer.item or "unknown",
            "unit_price": float(offer.unit_price) if offer.unit_price is not None else 0.0,
            "currency": offer.currency or "unknown",
            "delivery_days": int(offer.delivery_days) if offer.delivery_days is not None else 0,
            "payment_terms": offer.payment_terms or "unknown",
            "risk_assessment": offer.risk_assessment or "not_provided",
        }

        doc_id = str(uuid.uuid4())

        self.vector_store.add_document(
            doc_id=doc_id,
            text=offer.raw_text,
            embedding=embedding,
            metadata=metadata,
        )

        return doc_id

    def retrieve(self, query_text: str, top_k: int = 5) -> List[Offer]:
        """
        Retrieves semantically similar offers and converts them back into Offer objects.
        """
        query_embedding = self.embedder.embed_text(query_text)

        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k,
        )

        # Chroma returns lists of lists
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        offers: List[Offer] = []

        for doc_text, meta in zip(documents, metadatas):
            offers.append(
                Offer(
                    supplier=meta.get("supplier"),
                    item=meta.get("item"),
                    unit_price=meta.get("unit_price"),
                    currency=meta.get("currency"),
                    price_display=f"{meta.get('currency')}{meta.get('unit_price')}",
                    delivery_days=meta.get("delivery_days"),
                    payment_terms=meta.get("payment_terms"),
                    risk_assessment=meta.get("risk_assessment"),
                    internal_notes=None,
                    raw_text=doc_text,
                )
            )

        return offers


# -------------------------------------------------
# Singleton instance (shared across the application)
# -------------------------------------------------
retriever_agent = RetrieverAgent()
