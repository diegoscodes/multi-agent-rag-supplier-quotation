from app.services.llm_service import LLMService

text = """
Supplier: QuickFix Ltd
We offer 10mm steel bolts at €0.75 per unit.
Delivery time is 10 business days.
Payment terms: Net 45.
Supplier is reliable and low risk.
"""

llm = LLMService()

print("LLM enabled:", llm.enabled)

result = llm.extract_structured(text)

print("\n=== LLM RESULT ===")
for k, v in result.items():
    print(f"{k}: {v}")
