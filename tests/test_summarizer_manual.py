from app.agents.extractor_agent import ExtractorAgent
from app.agents.evaluator_agent import EvaluatorAgent



# --------------------------
# TEST TEXTS
# --------------------------
text1 = """
Supplier QuickFix
Quotation:
QuickFix offers the 10mm steel bolt at €0.75 per unit.
Delivery time is 10 business days.
Payment terms: Net 45.
"""

text2 = """
Supplier MetalWorks
Quotation:
MetalWorks offers the 10mm steel bolt at €0.68 per unit.
Delivery in 7 days.
Payment terms: Net 30.
"""


# --------------------------
# MANUAL TEST FUNCTION
# --------------------------
def run_test():
    extractor = ExtractorAgent()
    evaluator = EvaluatorAgent(use_llm=False)  # não chama LLM no teste
    summarizer = SummarizerAgent(requirement_description="Purchase of steel bolts")

    # Extract offers
    offers = [extractor.extract(text1), extractor.extract(text2)]

    # Evaluate offers
    evaluation_output = evaluator.evaluate(offers)

    # Final summary
    report = summarizer.summarize(offers, evaluation_output)

    # Print
    print("\n===== SUMMARY REPORT =====\n")
    print(report.model_dump())


# --------------------------
# RUN IF YOU RUN DIRECTLY
# --------------------------
if __name__ == "__main__":
    run_test()
