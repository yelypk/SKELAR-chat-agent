from __future__ import annotations

import re

TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)


def normalize_tokens(text: str, *, min_token_length: int = 3) -> set[str]:
    tokens = TOKEN_PATTERN.findall(text.casefold())
    return {token for token in tokens if len(token) >= min_token_length}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0
