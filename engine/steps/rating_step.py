from __future__ import annotations

from agents.customer import CustomerAgent
from engine.session import DialogueSession


def build_customer_rating_payload(session: DialogueSession) -> dict:
    return {
        "intent": session.intent.intent_id,
        "persona_seed_prompt": session.persona.persona_seed_prompt,
        "termination_reason": session.termination_reason,
        "transcript": [
            {
                "speaker": turn.speaker,
                "utterance": turn.utterance,
                "payload": turn.payload,
            }
            for turn in session.turns
        ],
    }


def apply_customer_rating(session: DialogueSession, agent: CustomerAgent) -> DialogueSession:
    payload = build_customer_rating_payload(session)
    rating = agent.rate_dialogue(payload)
    session.client_quality_score = rating.client_quality_score
    return session
