
from app.agents.extractor_agent import ExtractorAgent
from app.agents.retriever_agent import RetrieverAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.models.offer import Offer

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

# Recovery
results = ret.retrieve("10mm steel bolts reliable supplier", top_k=5)

offers_for_eval = []
for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
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

# To assess
evaluation = ev.evaluate(
    offers=offers_for_eval,
    user_query="10mm steel bolts reliable supplier"
)

print("\nBEST OFFER:")
print(evaluation["best_offer"])

print("\nREASONING:")
print(evaluation["reasoning"])

print("\nRANKING:")
for r in evaluation["ranking"]:
    print(r)
