from __future__ import annotations

from langchain_core.embeddings import Embeddings

from engine.rules.constants import (
    CUSTOMER_COMMITMENT_MARKERS,
    CUSTOMER_COMMITMENT_SHORT_MARKERS,
    CUSTOMER_LATER_PROGRESS_MARKERS,
    DEADLOCK_SIMILARITY_CAP,
)
from engine.rules.vector_utils import cosine_similarity
from engine.session import DialogueSession


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
        any(token in text for token in CUSTOMER_COMMITMENT_MARKERS)
        for text in recent_customer
    )
    has_no_progress_phrase = all(
        any(token in text for token in CUSTOMER_LATER_PROGRESS_MARKERS)
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
    support_similarity = cosine_similarity(support_vectors[-1], support_vectors[-2])
    customer_similarity = cosine_similarity(customer_vectors[-1], customer_vectors[-2])

    no_new_questions = len(set(session.asked_questions[-window:])) <= 1
    no_new_actions = len(set(session.support_proposed_actions[-window:])) <= 1
    effective_threshold = min(threshold, DEADLOCK_SIMILARITY_CAP)
    semantic_loop = (
        support_similarity >= effective_threshold
        and customer_similarity >= effective_threshold
        and no_new_questions
        and no_new_actions
    )

    customer_commitment_loop = all(
        any(token in text.lower() for token in CUSTOMER_COMMITMENT_SHORT_MARKERS)
        for text in recent_customer[-2:]
    )
    support_repetition_loop = no_new_actions and no_new_questions
    if support_repetition_loop and customer_commitment_loop:
        return True
    if _is_acknowledgement_loop(session, window=max(2, window)):
        return True
    return semantic_loop
