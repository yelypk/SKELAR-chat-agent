from __future__ import annotations

from engine.rules.constants import ESCALATION_RULE_SIM_THRESHOLD, HIGH_RISK_ESCALATION_MARKERS
from engine.rules.vector_utils import jaccard_similarity, normalize_tokens
from engine.session import DialogueSession


def should_allow_escalation(session: DialogueSession) -> bool:
    transcript_context = " ".join(turn.utterance for turn in session.turns)
    support_actions = " ".join(session.support_proposed_actions)
    asked_questions = " ".join(session.asked_questions)
    context_text = f"{transcript_context} {support_actions} {asked_questions}".casefold()
    context_tokens = normalize_tokens(context_text)

    # High-risk content should permit escalation even if intent rules are absent.
    if any(marker in context_text for marker in HIGH_RISK_ESCALATION_MARKERS):
        return True

    rules = session.support_view.get("escalation_rules", [])
    if not rules:
        # If intent has no explicit rules, still allow escalation in prolonged unresolved sessions.
        if session.turn_index >= max(4, session.max_turns - 2):
            return True
        return False
    # Require at least some troubleshooting before escalation.
    if len(session.asked_questions) < 1:
        return False
    if not session.support_proposed_actions:
        return False
    if session.turn_index >= max(4, session.max_turns - 2):
        return True
    if len(session.customer_confusion_events) >= 2:
        return True

    for rule in rules:
        rule_tokens = normalize_tokens(str(rule))
        if jaccard_similarity(rule_tokens, context_tokens) >= ESCALATION_RULE_SIM_THRESHOLD:
            return True

    return False
