from __future__ import annotations

from dataclasses import dataclass

from agents.customer import CustomerAgent
from agents.judge import JudgeAgent
from agents.json_protocol import InvalidLLMOutputError
from agents.support import SupportAgent
from langchain_core.embeddings import Embeddings

from engine.config import AppConfig
from engine.post_turn import finalize_turn
from engine.session import DialogueSession
from engine.state import TerminationReason
from engine.steps.customer_step import (
    apply_customer_output,
    build_customer_payload,
    run_customer_agent,
)
from engine.steps.judge_step import apply_judge
from engine.steps.rating_step import apply_customer_rating
from engine.steps.support_step import (
    apply_support_output,
    build_support_payload,
    run_support_agent,
)


@dataclass(frozen=True)
class AgentBundle:
    support: SupportAgent
    customer: CustomerAgent
    judge: JudgeAgent


@dataclass(frozen=True)
class RuntimeBundle:
    config: AppConfig
    embeddings: Embeddings


def run_dialogue(
    session: DialogueSession,
    agents: AgentBundle,
    runtime: RuntimeBundle,
) -> DialogueSession:
    while not session.is_terminal:
        try:
            customer_payload = build_customer_payload(session)
            customer_output = run_customer_agent(agents.customer, customer_payload)
        except InvalidLLMOutputError:
            session.termination_reason = TerminationReason.LLM_INVALID_JSON.value
            break

        apply_customer_output(session, customer_output)
        finalize_turn(session, runtime.embeddings, runtime.config)
        if session.is_terminal:
            break

        try:
            support_payload = build_support_payload(session)
            support_output = run_support_agent(agents.support, support_payload)
        except InvalidLLMOutputError:
            session.termination_reason = TerminationReason.LLM_INVALID_JSON.value
            break

        apply_support_output(session, support_output)
        finalize_turn(session, runtime.embeddings, runtime.config)

    try:
        apply_customer_rating(session, agents.customer)
    except InvalidLLMOutputError:
        session.client_quality_score = None

    fallback_termination = TerminationReason.LLM_INVALID_JSON.value
    try:
        apply_judge(session, agents.judge, fallback_termination=fallback_termination)
    except InvalidLLMOutputError:
        session.judge_output = {
            "resolved": False,
            "satisfaction": "unsatisfied",
            "quality_score": 1,
            "agent_mistakes": [],
            "termination_reason": fallback_termination,
            "rationale": "Judge failed to return valid JSON.",
        }
        session.judge_validation = {
            "resolved_match": False,
            "termination_match": False,
            "validated_mistakes": [],
            "missed_mistakes": [],
            "extra_mistakes": [],
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "notes": "Judge failed to return valid JSON.",
        }

    return session
