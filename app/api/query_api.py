from app.agents.retriever_agent import retriever_agent
from app.models.offer import Offer
from app.storage.offer_store import offer_store
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.evaluator_agent import EvaluatorAgent



router = APIRouter()

evaluator = EvaluatorAgent(use_llm=True)


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
def query_best_supplier(payload: QueryRequest):
    offers = retriever_agent.retrieve(payload.query, top_k=3)

    if not offers:
        return {"error": "No relevant offers found."}

    evaluation = evaluator.evaluate(
        offers=offers,
        user_query=payload.query,
    )

    return evaluation



