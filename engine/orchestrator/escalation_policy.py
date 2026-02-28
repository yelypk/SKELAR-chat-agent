from __future__ import annotations

import re

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


def should_allow_escalation(state: DialogueState) -> bool:
    rules = state["support_view"].get("escalation_rules", [])
    if not rules:
        # If intent has no explicit rules, still allow escalation in prolonged unresolved sessions.
        if state["turn_index"] >= max(4, state["max_turns"] - 2):
            return True
        return False
    # Require at least some troubleshooting before escalation.
    if len(state["asked_questions"]) < 1:
        return False
    if not state["support_proposed_actions"]:
        return False
    if state["turn_index"] >= max(4, state["max_turns"] - 2):
        return True
    if len(state["customer_confusion_events"]) >= 2:
        return True

    transcript_context = " ".join(turn["utterance"] for turn in state["turns"])
    support_actions = " ".join(state["support_proposed_actions"])
    asked_questions = " ".join(state["asked_questions"])
    context_text = f"{transcript_context} {support_actions} {asked_questions}".lower()
    context_tokens = _normalize_tokens(context_text)

    for rule in rules:
        rule_tokens = _normalize_tokens(str(rule))
        if _jaccard_similarity(rule_tokens, context_tokens) >= 0.12:
            return True

    # Fallback: explicit high-risk escalation triggers from the user context.
    high_risk_markers = (
        "fraud",
        "compliance",
        "security",
        "legal",
        "chargeback",
        "supervisor",
        "manager",
    )
    return any(marker in context_text for marker in high_risk_markers)
