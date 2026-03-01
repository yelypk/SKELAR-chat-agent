from __future__ import annotations

from agents.support import SupportAgent
from engine.orchestrator.escalation_policy import should_allow_escalation
from engine.session import DialogueSession
from engine.session_ops import append_support_turn, mark_escalated
from engine.state import SupportTurn


def _next_planned_mistake(session: DialogueSession) -> str:
    idx = session.support_turn_count
    if idx >= len(session.planned_mistakes):
        return "none"
    return session.planned_mistakes[idx]


def build_support_payload(session: DialogueSession) -> dict:
    return {
        "intent_card": session.support_view,
        "support_persona_seed_prompt": session.support_persona.support_persona_seed_prompt,
        "transcript": session.transcript_payload(),
        "planned_mistake": _next_planned_mistake(session),
        "dialogue_phase": session.dialogue_phase,
        "customer_confusion_events": session.confusion_events_payload(limit=3),
        "patience": session.patience,
        "trust": session.trust,
    }


def run_support_agent(agent: SupportAgent, payload: dict) -> SupportTurn:
    return agent.run_turn(payload)


def apply_support_output(session: DialogueSession, output: SupportTurn) -> None:
    append_support_turn(session, output)
    if output.should_escalate and should_allow_escalation(session):
        mark_escalated(session)
