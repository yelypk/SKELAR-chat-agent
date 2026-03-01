from __future__ import annotations

from engine.state import DialogueState
from engine.orchestrator.text_similarity import jaccard_similarity, normalize_tokens

ESCALATION_RULE_SIM_THRESHOLD = 0.12
HIGH_RISK_ESCALATION_MARKERS = (
    "fraud",
    "compliance",
    "security",
    "legal",
    "chargeback",
    "supervisor",
    "manager",
)

def should_allow_escalation(state: DialogueState) -> bool:
    transcript_context = " ".join(turn["utterance"] for turn in state["turns"])
    support_actions = " ".join(state["support_proposed_actions"])
    asked_questions = " ".join(state["asked_questions"])
    context_text = f"{transcript_context} {support_actions} {asked_questions}".casefold()
    context_tokens = normalize_tokens(context_text)

    # High-risk content should permit escalation even if intent rules are absent.
    if any(marker in context_text for marker in HIGH_RISK_ESCALATION_MARKERS):
        return True

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

    for rule in rules:
        rule_tokens = normalize_tokens(str(rule))
        if jaccard_similarity(rule_tokens, context_tokens) >= ESCALATION_RULE_SIM_THRESHOLD:
            return True

    return False
