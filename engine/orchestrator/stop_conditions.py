from __future__ import annotations

import math
import re
from typing import Sequence

from langchain_core.embeddings import Embeddings

from engine.state import DialogueState, TerminationReason


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


def _has_customer_turn(state: DialogueState) -> bool:
    return any(t["speaker"] == "customer" for t in state["turns"])


def _get_customer_turns(state: DialogueState) -> list[dict]:
    return [turn for turn in state["turns"] if turn["speaker"] == "customer"]


def _latest_customer_text(state: DialogueState) -> str:
    for turn in reversed(state["turns"]):
        if turn["speaker"] == "customer":
            return turn["utterance"].lower()
    return ""


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


def _has_support_closing_turn(state: DialogueState) -> bool:
    for turn in reversed(state["turns"]):
        if turn["speaker"] != "support":
            continue
        text = turn["utterance"].lower()
        has_offer = any(
            token in text
            for token in (
                "anything else",
                "else i can help",
                "can i help",
                "other issue",
            )
        )
        has_goodbye = any(
            token in text
            for token in (
                "goodbye",
                "have a nice day",
                "have a great day",
                "take care",
                "bye",
            )
        )
        return has_offer or has_goodbye
    return False


def _has_customer_follow_up(state: DialogueState) -> bool:
    return len(_get_customer_turns(state)) >= 2


def _is_acknowledgement_loop(state: DialogueState, window: int) -> bool:
    recent_support = [
        t["utterance"].lower() for t in state["turns"] if t["speaker"] == "support"
    ][-window:]
    recent_customer = [
        t["utterance"].lower() for t in state["turns"] if t["speaker"] == "customer"
    ][-window:]
    if len(recent_support) < window or len(recent_customer) < window:
        return False
    support_repeat = len(set(state["support_proposed_actions"][-window:])) <= 1
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
    state: DialogueState,
    embeddings: Embeddings,
    window: int,
    threshold: float,
) -> bool:
    if len(state["turns"]) < window * 2:
        return False
    recent_support = [
        t["utterance"] for t in state["turns"] if t["speaker"] == "support"
    ][-window:]
    recent_customer = [
        t["utterance"] for t in state["turns"] if t["speaker"] == "customer"
    ][-window:]
    if len(recent_support) < window or len(recent_customer) < window:
        return False

    support_vectors = embeddings.embed_documents(recent_support)
    customer_vectors = embeddings.embed_documents(recent_customer)
    support_similarity = _cosine_similarity(support_vectors[-1], support_vectors[-2])
    customer_similarity = _cosine_similarity(customer_vectors[-1], customer_vectors[-2])
    no_new_questions = len(set(state["asked_questions"][-window:])) <= 1
    no_new_actions = len(set(state["support_proposed_actions"][-window:])) <= 1
    # Cap similarity threshold to avoid missing obvious loops with minor paraphrases.
    effective_threshold = min(threshold, 0.85)
    semantic_loop = (
        support_similarity >= effective_threshold
        and customer_similarity >= effective_threshold
        and no_new_questions
        and no_new_actions
    )
    # Fallback: detect "acknowledgement loop" where customer repeatedly agrees to do
    # steps later and support repeats the same plan with no new progress.
    customer_commitment_loop = all(
        any(token in text.lower() for token in ("i'll", "i will", "thanks", "that works"))
        for text in recent_customer[-2:]
    )
    support_repetition_loop = no_new_actions and no_new_questions
    if support_repetition_loop and customer_commitment_loop:
        return True
    if _is_acknowledgement_loop(state, window=max(2, window)):
        return True
    return semantic_loop


def _is_resolved(state: DialogueState, embeddings: Embeddings) -> bool:
    # Require at least two customer turns:
    # 1) initial issue statement, 2) post-solution confirmation.
    customer_turns = _get_customer_turns(state)
    if len(customer_turns) < 2:
        return False
    if not state["turns"] or state["turns"][-1]["speaker"] != "customer":
        return False
    if not state["support_proposed_actions"]:
        return False
    latest_action = state["support_proposed_actions"][-1].lower()

    resolution_paths = state["intent"].resolution_paths
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
    customer_text = _latest_customer_text(state)
    customer_not_blocking = not _customer_blocks_resolution(customer_text)
    customer_confirmed = _customer_confirms_resolution(customer_text)
    return matched and customer_not_blocking and customer_confirmed


def compute_termination(state: DialogueState) -> str | None:
    # A one-sided exchange is not a valid dialogue session.
    if not _has_customer_turn(state):
        return None
    # Resolved dialogues should include a support-side closing turn.
    if state["resolved"] and _has_support_closing_turn(state):
        return TerminationReason.RESOLVED.value
    if state["escalated"] and _has_customer_follow_up(state):
        return TerminationReason.ESCALATION.value
    if state["customer_quit"]:
        return TerminationReason.CUSTOMER_QUIT.value
    if state["agent_quit"]:
        return TerminationReason.AGENT_QUIT.value
    if state["deadlock_detected"]:
        return TerminationReason.DEADLOCK.value
    if state["max_turns_reached"]:
        return TerminationReason.MAX_TURNS.value
    return None


def apply_stop_conditions(
    state: DialogueState,
    embeddings: Embeddings,
    deadlock_window: int,
    deadlock_threshold: float,
) -> None:
    state["resolved"] = _is_resolved(state, embeddings)
    state["max_turns_reached"] = state["turn_index"] >= state["max_turns"]
    state["deadlock_detected"] = detect_deadlock(
        state=state,
        embeddings=embeddings,
        window=deadlock_window,
        threshold=deadlock_threshold,
    )
    # Avoid unusable max-turn/deadlock tails: force managed escalation when unresolved.
    if (
        not state["resolved"]
        and not state["escalated"]
        and (state["deadlock_detected"] or state["max_turns_reached"])
    ):
        state["escalated"] = True
    state["termination_reason"] = compute_termination(state)
