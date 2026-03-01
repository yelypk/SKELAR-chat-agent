from __future__ import annotations

from typing import Literal

from engine.session import DialogueSession


def _latest_support_questions(session: DialogueSession) -> list[str]:
    for turn in reversed(session.turns):
        if turn.speaker != "support":
            continue
        questions = turn.payload.get("questions", [])
        if isinstance(questions, list):
            return [str(question) for question in questions]
        return []
    return []


def compute_dialogue_phase(
    session: DialogueSession,
) -> Literal["greeting", "diagnosis", "resolution_check", "closure"]:
    support_turns = len([turn for turn in session.turns if turn.speaker == "support"])
    customer_turns = len([turn for turn in session.turns if turn.speaker == "customer"])

    if session.termination_reason or session.resolved or session.escalated:
        return "closure"
    if session.customer_quit or session.agent_quit:
        return "closure"
    if support_turns == 0 or customer_turns == 0:
        return "greeting"

    latest_questions = _latest_support_questions(session)
    return "diagnosis" if latest_questions else "resolution_check"
