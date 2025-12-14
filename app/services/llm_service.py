import os
import json
import re
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """
    LLM Service compatible with OpenAI SDK >= 2.x (responses.create)

    - Defensive JSON parsing

    - Safe fallback

    - Never breaks pipeline

    - Production ready
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")

        self.client = None
        self.enabled = False

        if not self.api_key:
            print("❌ OPENAI_API_KEY not found")
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.enabled = True
        except Exception as e:
            print("❌ LLM init error:", e)

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _response_text(self, response) -> Optional[str]:
        """
        Normalizes text returned by responses.create (OpenAI)
        """
        try:
            if hasattr(response, "output_text") and response.output_text:
                return response.output_text.strip()

            parts = []
            for item in response.output:
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            parts.append(c.get("text", ""))

            return "\n".join(parts).strip() if parts else None
        except Exception as e:
            print("❌ Response parsing error:", e)
            return None

    def _safe_json_parse(self, text: str) -> Optional[dict]:
        """
        Extracts the first valid JSON from an LLM response.
        """
        if not text:
            return None

        # remove blocos ```json ``` se existirem
        text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()

        # tentativa direta
        try:
            return json.loads(text)
        except Exception:
            pass

        # tenta extrair bloco {...}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

        return None

    def _response_json(self, prompt: str) -> Optional[dict]:
        """
        LLM call that returns secure JSON.
        """
        if not self.enabled:
            return None

        try:
            resp = self.client.responses.create(
                model=self.model_name,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a data extraction engine. "
                            "Return ONLY a valid JSON object. "
                            "Do not add explanations or formatting."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

            text = self._response_text(resp)
            return self._safe_json_parse(text)

        except Exception as e:
            print("❌ LLM JSON error:", e)
            return None

    def _response_text_free(self, prompt: str) -> Optional[str]:
        """
        LLM Call for Free Text
        """
        if not self.enabled:
            return None

        try:
            resp = self.client.responses.create(
                model=self.model_name,
                input=prompt,
                temperature=0.2,
            )
            return self._response_text(resp)
        except Exception as e:
            print("❌ LLM text error:", e)
            return None

    # =========================================================
    # PUBLIC METHODS
    # =========================================================

    def extract_structured(self, text: str) -> dict:
        """
        Extracts structured data from a quote.
        """
        prompt = f"""
Extract supplier quotation data.

Return ONLY JSON with fields:
supplier, item, unit_price, currency, delivery_days, payment_terms, risk_assessment.

Rules:
- unit_price: number or null
- delivery_days: integer or null
- currency: €, $, £ or null

Text:
{text}
"""

        data = self._response_json(prompt)

        schema = {
            "supplier": None,
            "item": None,
            "unit_price": None,
            "currency": None,
            "delivery_days": None,
            "payment_terms": None,
            "risk_assessment": None,
        }

        if not isinstance(data, dict):
            return schema

        for k in schema:
            schema[k] = data.get(k)

        return schema

    def summarize_evaluation(
        self,
        user_query: str,
        scored_offers: List[Dict[str, Any]],
        best_offer: Dict[str, Any],
    ) -> str:
        """
        Provides a brief explanation of the decision.
        """
        if not self.enabled:
            return f"Best supplier: {best_offer.get('supplier')} (LLM disabled)"

        offers_summary = "\n".join(
            f"- {o['offer'].get('supplier')} | score={o['score']:.2f}"
            for o in scored_offers
        )

        # --- currency-safe price handling ---
        price_display = best_offer.get("price_display")
        currency = best_offer.get("currency")

        # fallback caso price_display não exista
        if not price_display:
            unit_price = best_offer.get("unit_price")
            if unit_price is not None and currency:
                price_display = f"{currency}{unit_price}"
        fastest_offer = None
        for entry in scored_offers:
            offer = entry["offer"]
            d = offer.get("delivery_days")
            if d is not None:
                if fastest_offer is None or d < fastest_offer.get("delivery_days", float("inf")):
                    fastest_offer = offer

        prompt = f"""
        User request:
        {user_query}

        Offers evaluated:
        {offers_summary}

        Best selected offer:
        Supplier: {best_offer.get('supplier')}
        Item: {best_offer.get('item')}
        Price: {best_offer.get('price_display')}
        Delivery days: {best_offer.get('delivery_days')}
        Risk information: {best_offer.get('risk_assessment') or "Not explicitly provided"}

        Fastest delivery option:
        Supplier: {fastest_offer.get('supplier') if fastest_offer else "Not available"}
        Price: {fastest_offer.get('price_display') if fastest_offer else "N/A"}
        Delivery days: {fastest_offer.get('delivery_days') if fastest_offer else "N/A"}

        Important guidance:
        - If another supplier meets the delivery requirement but was not selected, explicitly explain why.
        - Treat delivery time as a soft constraint unless the user explicitly states it is mandatory.
        - If risk information is missing or not explicitly provided, assume a neutral risk profile.
        - Do NOT state that there is "no risk".
        - Phrase risk-related conclusions as "no significant risk identified based on available information".

        Formatting rules:
        - Use plain text only
        - Do NOT use markdown, bullet points, or numbered lists
        - Write in short paragraphs
        - Separate paragraphs with a single line break
        - Do NOT start a sentence immediately after a line break

        Task:
        Provide a concise, professional explanation of why the best offer was selected.
        Explicitly compare it with the fastest delivery option if they are different suppliers.
        Focus on price, delivery time, and risk assumptions.
        

        Task:
        Provide a concise, professional explanation of why this offer was selected, focusing on price, delivery time, and risk assumptions.
        """



        text = self._response_text_free(prompt)

        if not text:
            return f"Best supplier: {best_offer.get('supplier')}"

        # Clean excessive line breaks (avoid '\n\nIn terms of...')
        text = re.sub(r"\n\s*\n+", "\n", text)
        text = text.strip()

        return text

