from __future__ import annotations

from agents.support import SupportAgent
from engine.config import AppConfig
from engine.orchestrator.escalation_policy import evaluate_escalation_policy
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


def apply_support_output(session: DialogueSession, output: SupportTurn, config: AppConfig) -> None:
    append_support_turn(session, output)
    policy_decision = evaluate_escalation_policy(session)
    llm_path_enabled = config.allow_llm_escalation

    session.last_escalation_decision = {
        "output_should_escalate": bool(output.should_escalate),
        "policy_allow": policy_decision.allow,
        "markers_hit": policy_decision.markers_hit,
        "matched_escalation_rule": policy_decision.matched_rule,
        "policy_reason": policy_decision.reason,
        "llm_path_enabled": llm_path_enabled,
        "escalated_after_turn": False,
    }

    if llm_path_enabled and output.should_escalate and policy_decision.allow:
        mark_escalated(session)
        session.last_escalation_decision["escalated_after_turn"] = True
