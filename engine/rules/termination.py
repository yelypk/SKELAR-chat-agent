from __future__ import annotations

from engine.rules.constants import (
    SUPPORT_CLOSING_GOODBYE_MARKERS,
    SUPPORT_CLOSING_OFFER_MARKERS,
)
from engine.session import DialogueSession
from engine.state import TerminationReason


def _has_customer_turn(session: DialogueSession) -> bool:
    return any(turn.speaker == "customer" for turn in session.turns)


def _has_support_closing_turn(session: DialogueSession) -> bool:
    for turn in reversed(session.turns):
        if turn.speaker != "support":
            continue
        text = turn.utterance.lower()
        has_offer = any(token in text for token in SUPPORT_CLOSING_OFFER_MARKERS)
        has_goodbye = any(token in text for token in SUPPORT_CLOSING_GOODBYE_MARKERS)
        return has_offer or has_goodbye
    return False


def _has_customer_follow_up(session: DialogueSession) -> bool:
    return len([turn for turn in session.turns if turn.speaker == "customer"]) >= 2


def compute_termination(session: DialogueSession) -> str | None:
    if not _has_customer_turn(session):
        return None
    if session.resolved and _has_support_closing_turn(session):
        return TerminationReason.RESOLVED.value
    if session.escalated and _has_customer_follow_up(session):
        return TerminationReason.ESCALATION.value
    if session.customer_quit:
        return TerminationReason.CUSTOMER_QUIT.value
    if session.agent_quit:
        return TerminationReason.AGENT_QUIT.value
    if session.deadlock_detected:
        return TerminationReason.DEADLOCK.value
    if session.max_turns_reached:
        return TerminationReason.MAX_TURNS.value
    return None
