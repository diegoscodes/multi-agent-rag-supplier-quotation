from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.retriever_agent import retriever_agent
from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.product_match_agent import ProductMatchAgent
from app.services.query_parsing import extract_target_item
from app.services.embeddings import EmbeddingService

router = APIRouter()

evaluator = EvaluatorAgent(use_llm=True)

# -------------------------------------------------
# Product matching dependencies (uses EmbeddingService)
# -------------------------------------------------
_embedder = EmbeddingService()


class EmbedAdapter:
    def __init__(self, embedder):
        self.embedder = embedder

    def embed(self, text: str):
        # EmbeddingService in this project exposes embed_text()
        return self.embedder.embed_text(text)


product_match_agent = ProductMatchAgent(llm_service=EmbedAdapter(_embedder), threshold=0.70)


class QueryRequest(BaseModel):
    query: str


def _match_log_to_json(log):
    """
    FastAPI can't JSON-serialize numpy.float32, numpy types, etc.
    Convert everything to native Python types.
    """
    return {
        "offer_id": str(log.offer_id),
        "offer_item": str(log.offer_item),
        "target_item": str(log.target_item),
        "similarity": float(log.similarity),
        "is_match": bool(log.is_match),
        "reason": str(log.reason),
    }


@router.post("/query")
def query_best_supplier(payload: QueryRequest):
    query_text = payload.query.strip()

    # 1) Parse query -> target product
    target_item = extract_target_item(query_text)

    # 2) Retrieve candidate offers
    offers = retriever_agent.retrieve(query_text, top_k=10)
    if not offers:
        return {
            "error": "No relevant offers found.",
            "target_item": target_item,
        }

    # ✅ Minimal guard: if no product could be extracted, don't run product matching
    if target_item == "unknown":
        return {
            "error": "Could not identify a target product in the query.",
            "target_item": target_item,
            "product_match": {
                "threshold": float(product_match_agent.threshold),
                "kept": 0,
                "rejected": len(offers),
                "logs": [],
            },
        }



    # 3) HARD business rule: product matching
    filtered_offers, match_logs = product_match_agent.validate_offers(
        target_item=target_item,
        offers=offers,
    )

    if not filtered_offers:
        return {
            "error": "No offers matched the requested product.",
            "target_item": target_item,
            "product_match": {
                "threshold": float(product_match_agent.threshold),
                "kept": 0,
                "rejected": len(offers),
                "logs": [_match_log_to_json(log) for log in match_logs],
            },
        }

    # 4) Evaluate only valid offers
    evaluation = evaluator.evaluate(
        offers=filtered_offers,
        user_query=query_text,
    )

    # 5) Final response with transparency
    return {
        **evaluation,
        "target_item": target_item,
        "product_match": {
            "threshold": float(product_match_agent.threshold),
            "kept": len(filtered_offers),
            "rejected": len(offers) - len(filtered_offers),
            "logs": [_match_log_to_json(log) for log in match_logs],
        },
    }
