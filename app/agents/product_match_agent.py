from dataclasses import dataclass
from typing import List, Tuple, Any
import math
import re

from app.models.offer import Offer


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tokens(text: str) -> List[str]:
    # keep simple word/number tokens
    return re.findall(r"[a-z0-9]+", (text or "").lower())


@dataclass
class MatchResult:
    offer_id: str
    offer_item: str
    target_item: str
    similarity: float
    is_match: bool
    reason: str


class ProductMatchAgent:
    """
    Hard gate: ensures offer.item matches the requested product (target_item).
    """

    def __init__(self, llm_service: Any, threshold: float = 0.78):
        """
        llm_service must expose: embed(text: str) -> List[float]
        """
        self.llm_service = llm_service
        self.threshold = threshold

        # Optional: slightly more forgiving for generic one-word items (e.g., "nails")
        self.short_item_threshold = min(threshold, 0.60)

        # Very generic words we should ignore in token overlap
        self.stop_tokens = {
            "item", "items", "product", "products", "set", "pack", "pcs", "pc",
            "unit", "units", "mm", "cm", "m", "kg", "g"
        }

    def validate_offers(
        self,
        target_item: str,
        offers: List[Offer],
    ) -> Tuple[List[Offer], List[MatchResult]]:
        target_item = (target_item or "").strip()
        target_vec = self.llm_service.embed(target_item)

        target_toks = [t for t in _tokens(target_item) if t not in self.stop_tokens]

        kept: List[Offer] = []
        logs: List[MatchResult] = []

        for offer in offers:
            offer_id = getattr(offer, "id", None) or f"{offer.supplier}-{offer.item}"

            offer_item = (offer.item or "").strip()
            if not offer_item:
                logs.append(MatchResult(
                    offer_id=str(offer_id),
                    offer_item=offer_item,
                    target_item=target_item,
                    similarity=0.0,
                    is_match=False,
                    reason="Offer item missing; rejected."
                ))
                continue

            offer_toks = [t for t in _tokens(offer_item) if t not in self.stop_tokens]

            # 1) Lexical shortcut: if the offer item token(s) appear in the target, accept.
            # Example: offer_item="nails" and target_item="galvanized nails 20mm" -> match
            overlap = set(offer_toks) & set(target_toks)
            if overlap:
                logs.append(MatchResult(
                    offer_id=str(offer_id),
                    offer_item=offer_item,
                    target_item=target_item,
                    similarity=1.0,
                    is_match=True,
                    reason=f"Matched by token overlap: {sorted(list(overlap))}"
                ))
                kept.append(offer)
                continue

            # 2) Fallback: embedding similarity (original behavior)
            offer_vec = self.llm_service.embed(offer_item)
            sim = cosine_similarity(target_vec, offer_vec)

            # If offer_item is very short/generic, use a slightly lower threshold
            thr = self.short_item_threshold if len(offer_toks) <= 1 else self.threshold

            is_match = sim >= thr
            reason = (
                "Matched by embedding similarity."
                if is_match
                else f"Rejected: low similarity (sim={sim:.3f} < thr={thr:.3f})."
            )

            logs.append(MatchResult(
                offer_id=str(offer_id),
                offer_item=offer_item,
                target_item=target_item,
                similarity=float(sim),
                is_match=bool(is_match),
                reason=reason,
            ))

            if is_match:
                kept.append(offer)

        return kept, logs
