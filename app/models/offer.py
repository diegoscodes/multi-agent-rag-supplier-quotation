from pydantic import BaseModel
from typing import Optional


class Offer(BaseModel):
    supplier: Optional[str]
    item: Optional[str]
    unit_price: Optional[float]
    currency: Optional[str] = None
    price_display: Optional[str] = None
    delivery_days: Optional[int]
    payment_terms: Optional[str]
    risk_assessment: Optional[str]
    internal_notes: Optional[str]
    raw_text: str
