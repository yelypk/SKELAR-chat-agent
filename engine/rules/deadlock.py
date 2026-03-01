from __future__ import annotations

import math
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


def _is_acknowledgement_loop(session: DialogueSession, window: int) -> bool:
    recent_support = [t.utterance.lower() for t in session.turns if t.speaker == "support"][
        -window:
    ]
    recent_customer = [t.utterance.lower() for t in session.turns if t.speaker == "customer"][
        -window:
    ]
    if len(recent_support) < window or len(recent_customer) < window:
        return False

    support_repeat = len(set(session.support_proposed_actions[-window:])) <= 1
    customer_commitment = all(
        any(token in text for token in ("i'll", "i will", "that works", "thanks", "okay"))
        for text in recent_customer
    )
    has_no_progress_phrase = all(
        any(token in text for token in ("upload", "later", "once", "when", "reply here"))
        for text in recent_customer
    )
    return support_repeat and customer_commitment and has_no_progress_phrase


def detect_deadlock(
    session: DialogueSession,
    embeddings: Embeddings,
    window: int,
    threshold: float,
) -> bool:
    if len(session.turns) < window * 2:
        return False

    recent_support = [t.utterance for t in session.turns if t.speaker == "support"][-window:]
    recent_customer = [t.utterance for t in session.turns if t.speaker == "customer"][-window:]
    if len(recent_support) < window or len(recent_customer) < window:
        return False

    support_vectors = embeddings.embed_documents(recent_support)
    customer_vectors = embeddings.embed_documents(recent_customer)
    support_similarity = _cosine_similarity(support_vectors[-1], support_vectors[-2])
    customer_similarity = _cosine_similarity(customer_vectors[-1], customer_vectors[-2])

    no_new_questions = len(set(session.asked_questions[-window:])) <= 1
    no_new_actions = len(set(session.support_proposed_actions[-window:])) <= 1
    effective_threshold = min(threshold, 0.85)
    semantic_loop = (
        support_similarity >= effective_threshold
        and customer_similarity >= effective_threshold
        and no_new_questions
        and no_new_actions
    )

    customer_commitment_loop = all(
        any(token in text.lower() for token in ("i'll", "i will", "thanks", "that works"))
        for text in recent_customer[-2:]
    )
    support_repetition_loop = no_new_actions and no_new_questions
    if support_repetition_loop and customer_commitment_loop:
        return True
    if _is_acknowledgement_loop(session, window=max(2, window)):
        return True
    return semantic_loop
