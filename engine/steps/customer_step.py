from __future__ import annotations

from agents.customer import CustomerAgent
from engine.session import DialogueSession
from engine.session_ops import append_customer_turn, mark_customer_quit
from engine.state import CustomerTurn


def build_customer_payload(session: DialogueSession) -> dict:
    return {
        "intent": session.intent.intent_id,
        "persona_seed_prompt": session.persona.persona_seed_prompt,
        "customer_context": session.customer_view,
        "transcript": session.transcript_payload(),
        "dialogue_phase": session.dialogue_phase,
        "patience": session.patience,
        "trust": session.trust,
    }


def run_customer_agent(agent: CustomerAgent, payload: dict) -> CustomerTurn:
    return agent.run_turn(payload)


def apply_customer_output(session: DialogueSession, output: CustomerTurn) -> None:
    append_customer_turn(session, output)
    if output.should_quit:
        mark_customer_quit(session)
