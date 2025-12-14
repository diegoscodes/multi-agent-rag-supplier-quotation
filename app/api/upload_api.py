from app.agents.retriever_agent import retriever_agent
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.agents.extractor_agent import ExtractorAgent
from app.storage.offer_store import offer_store

router = APIRouter()

extractor = ExtractorAgent()


class UploadRequest(BaseModel):
    texts: List[str]


@router.post("/upload")
def upload_offers(payload: UploadRequest):

    # Clear the Vector Store before each upload.
    retriever_agent.vector_store.reset()

    offers = [extractor.extract(t) for t in payload.texts]

    for offer in offers:
        retriever_agent.ingest_offer(offer)

    return {
        "message": f"{len(offers)} offers ingested successfully",
        "total_offers": len(offers),
    }


