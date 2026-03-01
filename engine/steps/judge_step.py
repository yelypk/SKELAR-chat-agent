from __future__ import annotations

from agents.judge import JudgeAgent
from engine.orchestrator.judge_validation import validate_judge_output
from engine.session import DialogueSession


def build_judge_payload(session: DialogueSession) -> dict:
    return {
        "intent": session.intent.intent_id,
        "client_quality_score": session.client_quality_score,
        "transcript": session.transcript_payload(),
    }


def apply_judge(
    session: DialogueSession,
    agent: JudgeAgent,
    *,
    fallback_termination: str,
) -> None:
    payload = build_judge_payload(session)
    judge_output = agent.evaluate(payload).model_dump()
    session.judge_output = judge_output
    session.judge_validation = validate_judge_output(
        judge_output=judge_output,
        observed_mistakes=session.observed_mistakes,
        resolved_gt=session.resolved,
        termination_reason_gt=session.termination_reason or fallback_termination,
    )
