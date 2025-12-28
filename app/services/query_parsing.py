import re
from typing import Optional

# Words/phrases that usually mark constraints, not the product itself
_CUTOFF_WORDS = r"""
    delivered|delivery|ship|shipping|dispatch|lead\s*time|leadtime|
    quickly|fast|asap|urgent|soon|
    within|in\s+\d+\s+days?|under\s+\d+\s+days?|
    by\s+\w+day|before\s+\w+day|
    price|cost|budget|cheapest|best\s+price|
    payment|terms|net\s*\d+|
    reliable|supplier|quote|quotation|offer
"""

# Common trailing filler words we don't want at the end of the product
_TRAILING_JUNK = r"(please|thanks|thank\s+you|now|today|quickly|fast|asap)$"# Tokens that should never be accepted as the extracted "product"

_BAD_SINGLE_TOKENS = {
    "best", "cheapest", "lowest",
    "supplier", "suppliers",
    "offer", "offers",
    "quote", "quotes", "quotation", "quotations",
    "option", "options", "choice", "choices",
    "for", "need", "want", "looking",
}

# Politeness / filler tokens
_JUNK_TOKENS = {"please", "pls", "thanks", "thank", "thankyou", "kindly", "asap"}




# Words that should never be accepted as the extracted "product"
_BAD_TOKENS = _BAD_SINGLE_TOKENS | {
    "option", "options", "choice", "choices", "supplier", "suppliers",
    "quote", "quotes", "quotation", "quotations", "offer", "offers",
    "best", "cheapest", "lowest"
}


def _clean(text: str) -> str:
    text = (text or "").strip()
    # remove quotes/punctuation at ends
    text = re.sub(r"^[\s\"'\-:,;]+|[\s\"'\-:,;]+$", "", text)
    # collapse spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _cut_at_constraints(text: str) -> str:
    """
    Cuts the extracted candidate when constraints start (delivery, time, payment, etc.)
    """
    if not text:
        return text

    # Cut at punctuation separators if they likely start constraints
    parts = re.split(r"[,\.;:]\s*", text, maxsplit=1)
    left = parts[0]

    # Also cut at first occurrence of cutoff keywords
    m = re.search(rf"\b({_CUTOFF_WORDS})\b", text, flags=re.IGNORECASE | re.VERBOSE)
    if m:
        left = text[: m.start()]

    left = _clean(left)

    # remove trailing junk words
    left = re.sub(_TRAILING_JUNK, "", left, flags=re.IGNORECASE).strip()
    left = _clean(left)
    return left


def _is_bad_candidate(candidate: str) -> bool:
    if not candidate:
        return True

    tokens = [t.strip().lower() for t in candidate.split() if t.strip()]
    if not tokens:
        return True

    # If EVERYTHING is junk/bad tokens, it's not a product
    if all(t in _BAD_TOKENS or t in _JUNK_TOKENS for t in tokens):
        return True

    # keep your original protection for single-token bad candidates
    if len(tokens) == 1 and tokens[0] in _BAD_SINGLE_TOKENS:
        return True

    return False



def extract_target_item(query: str) -> str:
    """
    Extract a target product/item string from a user query.

    Examples:
    - "Need 10mm steel bolts delivered quickly" -> "10mm steel bolts"
    - "Looking for galvanized nails 20mm, delivery within 7 days" -> "galvanized nails 20mm"
    - "best supplier for 10mm steel bolts" -> "10mm steel bolts"
    """
    q = _clean(query).lower()

    # 1) Strong patterns: "need X", "looking for X", ...
    patterns = [
        r"\bneed\s+(?P<item>.+)$",
        r"\blooking\s+for\s+(?P<item>.+)$",
        r"\bwant\s+(?P<item>.+)$",
        r"\bbuy\s+(?P<item>.+)$",
        r"\bquote\s+for\s+(?P<item>.+)$",
        r"\bquotation\s+for\s+(?P<item>.+)$",
        r"\border\s+(?P<item>.+)$",
        r"\bpurchase\s+(?P<item>.+)$",
        r"\brequire\s+(?P<item>.+)$",
        r"\brequiring\s+(?P<item>.+)$",
    ]

    for pat in patterns:
        m = re.search(pat, q, flags=re.IGNORECASE)
        if m:
            candidate = _clean(m.group("item"))
            candidate = _cut_at_constraints(candidate)
            if candidate and not _is_bad_candidate(candidate):
                return candidate

    # ✅ NEW: "for X" patterns (fixes: "best supplier for X")
    for_patterns = [
        r"\bfor\s+(?P<item>.+)$",
        r"\bfor\s+the\s+(?P<item>.+)$",
        r"\bto\s+buy\s+(?P<item>.+)$",
        r"\bto\s+purchase\s+(?P<item>.+)$",
    ]
    for pat in for_patterns:
        m = re.search(pat, q, flags=re.IGNORECASE)
        if m:
            candidate = _clean(m.group("item"))
            candidate = _cut_at_constraints(candidate)
            if candidate and not _is_bad_candidate(candidate):
                return candidate

    # 2) Secondary patterns: chunk before cutoff words
    m = re.search(
        rf"(?P<item>.+?)\s+\b({_CUTOFF_WORDS})\b",
        q,
        flags=re.IGNORECASE | re.VERBOSE,
    )
    if m:
        candidate = _clean(m.group("item"))
        candidate = _cut_at_constraints(candidate)
        if candidate and not _is_bad_candidate(candidate):
            return candidate

    # 3) Fallback: remove constraints and keep remaining
    q2 = re.sub(rf"\b({_CUTOFF_WORDS})\b", " ", q, flags=re.IGNORECASE | re.VERBOSE)
    q2 = _clean(q2)

    tokens = q2.split()
    if len(tokens) > 6:
        q2 = " ".join(tokens[-4:])

    q2 = _clean(q2)
    if _is_bad_candidate(q2):
        return "unknown"
    return q2 or "unknown"
