import re
from typing import Optional
from app.models.offer import Offer
from app.services.llm_service import LLMService


class ExtractorAgent:
    def __init__(self):
        self.llm = LLMService()

    # -----------------------
    #  REGEX HELPERS
    # -----------------------
    def _extract_supplier(self, text: str) -> Optional[str]:
        patterns = [
            r"supplier\s+([A-Za-z0-9\- ]+)",
            r"from\s+([A-Za-z0-9\- ]+)",
            r"called\s+([A-Za-z0-9\- ]+)",
            r"name\s+was\s+([A-Za-z0-9\- ]+)",
            r"think\s+called\s+([A-Za-z0-9\- ]+)",
            r"company\s+([A-Za-z0-9\- ]+)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_item(self, text: str) -> Optional[str]:
        m = re.search(r"\bbolt[s]?\b", text, re.IGNORECASE)
        return "bolts" if m else None

    def _extract_unit_price(self, text: str):
        # euro
        m = re.search(r"(\d+(\.\d+)?)\s*€", text)
        if m:
            return float(m.group(1)), "€"

        # dollar
        m = re.search(r"\$(\d+(\.\d+)?)", text)
        if m:
            return float(m.group(1)), "$"

        # cents
        m = re.search(r"(\d+(\.\d+)?)\s*cents", text)
        if m:
            return float(m.group(1)) / 100, "$"

        return None, None

    def _extract_delivery_days(self, text: str):
        m = re.search(r"(\d+)\s*days", text, re.IGNORECASE)
        return int(m.group(1)) if m else None

    def _extract_payment_terms(self, text: str):
        m = re.search(r"net\s*\d+", text, re.IGNORECASE)
        return m.group(0).strip() if m else "Unknown"

    # -----------------------
    #  MAIN EXTRACT FUNCTION
    # -----------------------
    def extract(self, text: str) -> Offer:
        """
        Hybrid extraction:
        1. Try REGEX
        2. If REGEX misses critical fields → LLM fallback
        3. Merge regex + LLM results safely
        """

        # ---------- REGEX ----------
        raw_supplier = self._extract_supplier(text)
        supplier = self._clean_supplier_name(raw_supplier)

        item = self._extract_item(text)

        # IMPORTANT: extract price and currency ONCE
        price, currency = self._extract_unit_price(text)

        delivery = self._extract_delivery_days(text)
        payment = self._extract_payment_terms(text)

        # ---------- NEED LLM FALLBACK? ----------
        missing_critical = (
                supplier is None
                or price is None
                or delivery is None
        )

        llm_data = {}
        if missing_critical and self.llm.enabled:
            llm_data = self.llm.extract_structured(text) or {}

        # ---------- MERGE RESULTS ----------
        final_supplier = supplier or llm_data.get("supplier") or "Unknown Supplier"
        final_item = item or llm_data.get("item") or "Unknown Item"
        final_price = price if price is not None else llm_data.get("unit_price")
        final_currency = currency or llm_data.get("currency")
        final_delivery = delivery if delivery is not None else llm_data.get("delivery_days")
        final_payment = (
            payment if payment != "Unknown"
            else llm_data.get("payment_terms") or "Unknown"
        )
        final_risk = llm_data.get("risk_assessment", "Medium Risk")

        # ---------- PRICE DISPLAY ----------
        price_display = (
            f"{final_currency}{final_price:.2f}"
            if final_price is not None and final_currency
            else None
        )

        # ---------- DEFAULT FALLBACK ----------
        if final_price is None or final_delivery is None:
            return Offer(
                supplier=final_supplier,
                item=final_item,
                unit_price=final_price or 0,
                currency=final_currency,
                price_display=price_display,
                delivery_days=final_delivery or 999,
                payment_terms=final_payment,
                risk_assessment=final_risk,
                internal_notes=None,
                raw_text=text,
            )

        # ---------- SUCCESS ----------
        return Offer(
            supplier=final_supplier,
            item=final_item,
            unit_price=final_price,
            currency=final_currency,
            price_display=price_display,
            delivery_days=final_delivery,
            payment_terms=final_payment,
            risk_assessment=final_risk,
            internal_notes=None,
            raw_text=text,
        )

    def _clean_supplier_name(self, name: str | None) -> str | None:
        if not name:
            return None

        stop_words = [
            " offers",
            " offer",
            " provides",
            " providing",
            " supplying",
            " at"
        ]

        lower = name.lower()
        for w in stop_words:
            if w in lower:
                name = name[: lower.index(w)]
                break

        return name.strip()
