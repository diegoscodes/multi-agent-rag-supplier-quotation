from app.agents.product_match_agent import ProductMatchAgent
from app.models.offer import Offer


class FakeLLMService:
    def embed(self, text: str):
        t = (text or "").lower()
        if "bolt" in t:
            return [1.0, 0.0, 0.0]
        if "nail" in t:
            return [0.0, 1.0, 0.0]
        if "screw" in t:
            return [0.0, 0.0, 1.0]
        return [0.0, 0.0, 0.0]


def mk_offer(supplier: str, item: str | None, price: float, raw: str) -> Offer:
    return Offer(
        supplier=supplier,
        item=item,
        unit_price=price,
        currency="$",
        price_display=f"${price}",
        delivery_days=10,
        payment_terms="Net 45",
        risk_assessment="not_provided",
        internal_notes=None,
        raw_text=raw,
    )


def test_product_match_keeps_only_matching_items():
    agent = ProductMatchAgent(llm_service=FakeLLMService(), threshold=0.78)

    offers = [
        mk_offer("A", "10mm steel bolt", 0.75, "x"),
        mk_offer("B", "galvanized nails 20mm", 0.30, "y"),
        mk_offer("C", "wood screws set", 1.20, "z"),
    ]

    kept, logs = agent.validate_offers(target_item="steel bolts", offers=offers)

    assert len(kept) == 1
    assert "bolt" in kept[0].item.lower()
    assert len(logs) == 3
    assert any("nail" in l.offer_item.lower() and not l.is_match for l in logs)
    assert any("screw" in l.offer_item.lower() and not l.is_match for l in logs)


def test_product_match_rejects_missing_item_field():
    agent = ProductMatchAgent(llm_service=FakeLLMService(), threshold=0.78)

    offers = [mk_offer("X", None, 0.10, "x")]

    kept, logs = agent.validate_offers(target_item="nails", offers=offers)

    assert kept == []
    assert len(logs) == 1
    assert not logs[0].is_match
    assert "missing" in logs[0].reason.lower()
