from app.agents.extractor_agent import ExtractorAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.models.offer import Offer


def _iter_hits(results):
    """
    Supports:
    - list of Offer: [Offer(...), ...]
    - list of dict hits: [{"document": "...", "metadata": {...}}, ...]
    - chroma raw dict: {"documents":[...], "metadatas":[...]}
    """
    # Chroma raw dict format
    if isinstance(results, dict) and "documents" in results and "metadatas" in results:
        for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
            yield meta, doc
        return

    # ✅ NEW: list of Offer objects
    if isinstance(results, list) and results and isinstance(results[0], Offer):
        for o in results:
            meta = {
                "supplier": o.supplier,
                "item": o.item,
                "unit_price": o.unit_price,
                "delivery_days": o.delivery_days,
                "payment_terms": o.payment_terms,
                "risk_assessment": o.risk_assessment,
                "currency": getattr(o, "currency", None),
            }
            doc = o.raw_text or ""
            yield meta, doc
        return

    # Normalized list of hits format
    if isinstance(results, list):
        for r in results:
            if isinstance(r, dict):
                meta = r.get("metadata", {}) or {}
                doc = r.get("document", "") or ""
                yield meta, doc
        return

    raise TypeError(f"Unknown results format: {type(results)}")



def test_pipeline_end_to_end():
    ex = ExtractorAgent()
    ret = RetrieverAgent()
    ev = EvaluatorAgent(use_llm=False)

    text1 = """
    Supplier QuickFix
    Quotation:
    QuickFix offers the 10mm steel bolt at $0.75 per unit.
    Delivery time is 10 business days.
    Payment terms: Net 45.
    Internal Note:
    Reliable and consistent supplier.
    """

    text2 = """
    Supplier BudgetBolts
    Quotation:
    BudgetBolts offers the 10mm steel bolt at $0.65 per unit.
    Delivery time is 15 business days.
    Payment terms: Net 30.
    Internal Note:
    Some minor past quality issues, but generally acceptable.
    """

    # Extract
    offer1 = ex.extract(text1)
    offer2 = ex.extract(text2)

    # Ingestion
    ret.ingest_offer(offer1)
    ret.ingest_offer(offer2)

    # Retrieve
    results = ret.retrieve("10mm steel bolts reliable supplier", top_k=5)

    assert results is not None
    assert isinstance(results, (list, dict))

    offers_for_eval = []
    for meta, doc in _iter_hits(results):
        offers_for_eval.append(
            Offer(
                supplier=meta.get("supplier"),
                item=meta.get("item"),
                unit_price=meta.get("unit_price"),
                delivery_days=meta.get("delivery_days"),
                payment_terms=meta.get("payment_terms"),
                risk_assessment=meta.get("risk_assessment"),
                internal_notes=None,
                raw_text=doc,
            )
        )

    assert len(offers_for_eval) > 0

    evaluation = ev.evaluate(
        offers=offers_for_eval,
        user_query="10mm steel bolts reliable supplier"
    )

    assert "best_offer" in evaluation
    assert "ranking" in evaluation
    assert evaluation["best_offer"] is not None
    assert len(evaluation["ranking"]) > 0
