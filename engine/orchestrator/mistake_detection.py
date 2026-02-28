from __future__ import annotations

import re

from engine.orchestrator.escalation_policy import should_allow_escalation
from engine.state import DialogueState


def _normalize_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if len(word) > 2}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def _contains_rude_tone(state: DialogueState) -> bool:
    rude_markers = {
        "stupid",
        "dumb",
        "obvious",
        "your fault",
        "nonsense",
        "can't you read",
        "stop wasting",
    }
    for turn in state["turns"]:
        if turn["speaker"] != "support":
            continue
        text = turn["utterance"].lower()
        if any(marker in text for marker in rude_markers):
            return True
    return False


def _contains_forbidden_action(state: DialogueState) -> bool:
    forbidden = state["support_view"].get("forbidden_actions", [])
    if not forbidden:
        return False
    forbidden_tokens = [_normalize_tokens(item) for item in forbidden]
    for action in state["support_proposed_actions"]:
        action_tokens = _normalize_tokens(action)
        for rule_tokens in forbidden_tokens:
            if _jaccard_similarity(action_tokens, rule_tokens) >= 0.22:
                return True
    return False


def _ignored_required_questions(state: DialogueState) -> bool:
    required_questions = state["support_view"].get("required_questions", [])
    if not required_questions:
        return False
    asked = " ".join(state["asked_questions"])
    asked_tokens = _normalize_tokens(asked)
    if not asked_tokens:
        return True
    missed = 0
    for question in required_questions:
        rule_tokens = _normalize_tokens(question)
        if _jaccard_similarity(asked_tokens, rule_tokens) < 0.15:
            missed += 1
    return missed > 0


def _support_attempted_escalation(state: DialogueState) -> bool:
    for turn in state["turns"]:
        if turn["speaker"] != "support":
            continue
        payload = turn.get("payload", {})
        if payload.get("should_escalate") is True:
            return True
    return False


def _unnecessary_escalation(state: DialogueState) -> bool:
    if not _support_attempted_escalation(state):
        return False
    return not should_allow_escalation(state)


def detect_observed_mistakes(state: DialogueState) -> list[str]:
    observed: list[str] = []
    if _ignored_required_questions(state):
        observed.append("ignored_question")
    if _contains_forbidden_action(state):
        observed.append("incorrect_info")
    if _contains_rude_tone(state):
        observed.append("rude_tone")
    if state.get("termination_reason") and state.get("termination_reason") != "resolved":
        observed.append("no_resolution")
    if _unnecessary_escalation(state):
        observed.append("unnecessary_escalation")
    return sorted(set(observed))
