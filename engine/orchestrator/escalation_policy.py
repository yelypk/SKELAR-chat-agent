from __future__ import annotations

from dataclasses import dataclass

from engine.rules.constants import ESCALATION_RULE_SIM_THRESHOLD, HIGH_RISK_ESCALATION_MARKERS
from engine.rules.vector_utils import jaccard_similarity, normalize_tokens
from engine.session import DialogueSession


@dataclass(frozen=True)
class EscalationDecision:
    allow: bool
    markers_hit: list[str]
    matched_rule: str | None
    reason: str


def evaluate_escalation_policy(session: DialogueSession) -> EscalationDecision:
    transcript_context = " ".join(turn.utterance for turn in session.turns)
    support_actions = " ".join(session.support_proposed_actions)
    asked_questions = " ".join(session.asked_questions)
    context_text = f"{transcript_context} {support_actions} {asked_questions}".casefold()
    context_tokens = normalize_tokens(context_text)

    markers_hit = [
        marker for marker in HIGH_RISK_ESCALATION_MARKERS if marker in context_text
    ]
    # High-risk content should permit escalation even if intent rules are absent.
    if markers_hit:
        return EscalationDecision(
            allow=True,
            markers_hit=markers_hit,
            matched_rule=None,
            reason="high_risk_marker",
        )

    rules = session.support_view.get("escalation_rules", [])
    if not rules:
        return EscalationDecision(
            allow=False,
            markers_hit=[],
            matched_rule=None,
            reason="no_intent_rules",
        )

    # Require meaningful troubleshooting before escalation.
    if len(session.asked_questions) < 2:
        return EscalationDecision(
            allow=False,
            markers_hit=[],
            matched_rule=None,
            reason="insufficient_questions",
        )
    if not session.support_proposed_actions:
        return EscalationDecision(
            allow=False,
            markers_hit=[],
            matched_rule=None,
            reason="no_support_actions",
        )

    for rule in rules:
        rule_tokens = normalize_tokens(str(rule))
        if jaccard_similarity(rule_tokens, context_tokens) >= ESCALATION_RULE_SIM_THRESHOLD:
            return EscalationDecision(
                allow=True,
                markers_hit=[],
                matched_rule=str(rule),
                reason="rule_match",
            )

    return EscalationDecision(
        allow=False,
        markers_hit=[],
        matched_rule=None,
        reason="no_rule_match",
    )


def should_allow_escalation(session: DialogueSession) -> bool:
    return evaluate_escalation_policy(session).allow
