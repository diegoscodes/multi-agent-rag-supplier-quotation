import os
from typing import List, Dict, Any

from app.models.offer import Offer
from app.services.llm_service import LLMService


class EvaluatorAgent:
    """
    Compares multiple supplier offers and selects the best one
    based on price, delivery time, and risk profile.
    Optionally generates a textual reasoning using an LLM.
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self.llm = LLMService() if use_llm else None

        # Weights configurable via .env
        self.w_price = float(os.getenv("WEIGHT_PRICE", "0.5"))
        self.w_delivery = float(os.getenv("WEIGHT_DELIVERY", "0.3"))
        self.w_risk = float(os.getenv("WEIGHT_RISK", "0.2"))

        # Normalize weights so they always sum to 1.0
        total = self.w_price + self.w_delivery + self.w_risk
        if total > 0:
            self.w_price /= total
            self.w_delivery /= total
            self.w_risk /= total

    def _compute_scores(self, offers: List[Offer]) -> List[Dict[str, Any]]:
        """
        Computes a numerical score for each offer.
        Higher score means a better offer.
        """

        # ----------------------------------
        # Prepare values for normalization
        # ----------------------------------
        prices = [o.unit_price for o in offers if o.unit_price is not None]
        delivery_days = [o.delivery_days for o in offers if o.delivery_days is not None]

        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
        min_delivery = min(delivery_days) if delivery_days else None
        max_delivery = max(delivery_days) if delivery_days else None



        # ----------------------------------
        # Normalization helper function
        # Lower value = better score
        # ----------------------------------
        def normalize_better_lower(value, vmin, vmax, missing_score=0.2, tie_score=1.0):
            """
            Normalizes a value where lower is better:
            - Lowest value  -> 1.0
            - Highest value -> 0.0
            - Tie (vmin == vmax) -> tie_score
            - Missing value -> missing_score
            """
            if value is None:
                return missing_score
            if vmin is None or vmax is None:
                return missing_score
            if vmax == vmin:
                return tie_score
            return 1.0 - (value - vmin) / (vmax - vmin)

        scored: List[Dict[str, Any]] = []

        # ----------------------------------
        # Score each offer
        # ----------------------------------
        for offer in offers:
            # PRICE SCORE (lower price is better)
            price_score = round(
                normalize_better_lower(offer.unit_price, min_price, max_price), 2
            )
            price_score = max(price_score, 0.1)

            # DELIVERY SCORE (faster delivery is better)
            delivery_score = round(
                normalize_better_lower(
                    offer.delivery_days, min_delivery, max_delivery
                ),
                2,
            )
            delivery_score = max(delivery_score, 0.1)

            # RISK SCORE (derived from text)
            risk_raw = (offer.risk_assessment or "").lower()
            if "low" in risk_raw:
                risk_score = 1.0
            elif "high" in risk_raw:
                risk_score = 0.0
            else:
                risk_score = 0.5

            # Penalize advance or prepaid payment terms
            payment_raw = (offer.payment_terms or "").lower()
            if "advance" in payment_raw or "prepaid" in payment_raw:
                risk_score = round(risk_score * 0.7, 2)

            # FINAL SCORE (weighted sum)
            total_score = (
                self.w_price * price_score
                + self.w_delivery * delivery_score
                + self.w_risk * risk_score
            )

            scored.append(
                {
                    "offer": offer.model_dump(),
                    "score": round(float(total_score), 4),
                    "components": {
                        "price_score": price_score,
                        "delivery_score": delivery_score,
                        "risk_score": risk_score,
                    },
                }
            )

        # Sort offers by score (descending)
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def evaluate(
        self,
        offers: List[Offer],
        user_query: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluates a list of offers and returns:
        - best_offer
        - full ranking with scores
        - textual reasoning
        """

        if not offers:
            return {
                "best_offer": None,
                "ranking": [],
                "reasoning": "No offers available for evaluation.",
            }

        scored_offers = self._compute_scores(offers)
        best_entry = scored_offers[0]
        best_offer = best_entry["offer"]

        if self.use_llm and self.llm is not None:
            reasoning = self.llm.summarize_evaluation(
                user_query=user_query,
                scored_offers=scored_offers,
                best_offer=best_offer,
            )
        else:
            reasoning = (
                f"Best supplier: {best_offer.get('supplier')} "
                f"based on a weighted combination of price, delivery time, and risk."
            )

        return {
            "best_offer": best_offer,
            "ranking": scored_offers,
            "reasoning": reasoning,
        }
