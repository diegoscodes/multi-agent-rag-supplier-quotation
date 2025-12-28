from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.agents.extractor_agent import ExtractorAgent
from app.agents.retriever_agent import retriever_agent
from app.models.offer import Offer

router = APIRouter()
extractor = ExtractorAgent()


class UploadRequest(BaseModel):
    texts: List[str]


@router.post("/upload")
def upload_quotations(payload: UploadRequest):
    if not payload.texts:
        return {"error": "No quotation texts provided."}
    retriever_agent.reset_store()

    ingested = []
    errors = []

    for idx, text in enumerate(payload.texts):
        try:
            offer: Offer = extractor.extract(text)
            doc_id = retriever_agent.ingest_offer(offer)

            ingested.append({
                "index": idx,
                "doc_id": doc_id,
                "supplier": offer.supplier,
                "item": offer.item,
                "unit_price": offer.unit_price,
                "delivery_days": offer.delivery_days,
            })
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    return {
        "uploaded": len(ingested),
        "failed": len(errors),
        "ingested": ingested,
        "errors": errors,
    }
