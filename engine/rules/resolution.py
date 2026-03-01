from __future__ import annotations

import math
import re
from typing import Sequence

from langchain_core.embeddings import Embeddings

from engine.session import DialogueSession


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _normalize_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) > 2}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def _customer_blocks_resolution(text: str) -> bool:
    return any(
        token in text
        for token in (
            "still",
            "not working",
            "didn't help",
            "same issue",
            "not fixed",
            "doesn't work",
        )
    )


def _customer_confirms_resolution(text: str) -> bool:
    return any(
        token in text
        for token in (
            "thanks",
            "thank you",
            "that worked",
            "works now",
            "fixed",
            "resolved",
            "got it",
            "perfect",
            "all good",
        )
    )


def is_resolved(session: DialogueSession, embeddings: Embeddings) -> bool:
    customer_turns = [turn for turn in session.turns if turn.speaker == "customer"]
    if len(customer_turns) < 2:
        return False
    if not session.turns or session.turns[-1].speaker != "customer":
        return False
    if not session.support_proposed_actions:
        return False

    latest_action = session.support_proposed_actions[-1].lower()
    resolution_paths = session.intent.resolution_paths
    docs = [latest_action, *resolution_paths]
    vectors = embeddings.embed_documents(docs)
    latest_vector = vectors[0]
    path_vectors = vectors[1:]

    embedding_match = False
    lexical_match = False
    latest_tokens = _normalize_tokens(latest_action)
    for resolution, vector in zip(resolution_paths, path_vectors):
        sim = _cosine_similarity(latest_vector, vector)
        jac = _jaccard_similarity(latest_tokens, _normalize_tokens(resolution))
        if sim >= 0.86:
            embedding_match = True
        if jac >= 0.22:
            lexical_match = True
        if embedding_match and lexical_match:
            break

    matched = embedding_match or lexical_match
    latest_customer_text = customer_turns[-1].utterance.lower()
    customer_not_blocking = not _customer_blocks_resolution(latest_customer_text)
    customer_confirmed = _customer_confirms_resolution(latest_customer_text)
    return matched and customer_not_blocking and customer_confirmed
