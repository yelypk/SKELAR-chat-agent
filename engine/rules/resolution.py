from __future__ import annotations

from langchain_core.embeddings import Embeddings

from engine.rules.constants import (
    RESOLUTION_BLOCKERS,
    RESOLUTION_CONFIRMATIONS,
    RESOLUTION_EMBEDDING_THRESHOLD,
    RESOLUTION_LEXICAL_THRESHOLD,
)
from engine.rules.vector_utils import cosine_similarity, jaccard_similarity, normalize_tokens
from engine.session import DialogueSession


def _customer_blocks_resolution(text: str) -> bool:
    return any(token in text for token in RESOLUTION_BLOCKERS)


def _customer_confirms_resolution(text: str) -> bool:
    return any(token in text for token in RESOLUTION_CONFIRMATIONS)


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
    latest_vector = embeddings.embed_documents([latest_action])[0]
    path_vectors = session.ensure_resolution_path_vectors(embeddings)

    embedding_match = False
    lexical_match = False
    latest_tokens = normalize_tokens(latest_action)
    for resolution, vector in zip(resolution_paths, path_vectors):
        sim = cosine_similarity(latest_vector, vector)
        jac = jaccard_similarity(latest_tokens, normalize_tokens(resolution))
        if sim >= RESOLUTION_EMBEDDING_THRESHOLD:
            embedding_match = True
        if jac >= RESOLUTION_LEXICAL_THRESHOLD:
            lexical_match = True
        if embedding_match and lexical_match:
            break

    matched = embedding_match or lexical_match
    latest_customer_text = customer_turns[-1].utterance.lower()
    customer_not_blocking = not _customer_blocks_resolution(latest_customer_text)
    customer_confirmed = _customer_confirms_resolution(latest_customer_text)
    return matched and customer_not_blocking and customer_confirmed
