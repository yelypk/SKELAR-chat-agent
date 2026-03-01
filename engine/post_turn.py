from __future__ import annotations

from langchain_core.embeddings import Embeddings

from engine.config import AppConfig
from engine.rules.deadlock import detect_deadlock
from engine.rules.dialogue_phase import compute_dialogue_phase
from engine.rules.mistakes import detect_observed_mistakes
from engine.rules.resolution import is_resolved
from engine.rules.termination import compute_termination
from engine.session import DialogueSession


def finalize_turn(
    session: DialogueSession,
    embeddings: Embeddings,
    config: AppConfig,
) -> None:
    session.resolved = is_resolved(session, embeddings)
    session.max_turns_reached = session.turn_index >= session.max_turns
    session.deadlock_detected = detect_deadlock(
        session=session,
        embeddings=embeddings,
        window=config.deadlock_window,
        threshold=config.deadlock_similarity_threshold,
    )
    if (
        not session.resolved
        and not session.escalated
        and (session.deadlock_detected or session.max_turns_reached)
    ):
        session.escalated = True
    session.termination_reason = compute_termination(session)
    session.observed_mistakes = detect_observed_mistakes(session)
    session.dialogue_phase = compute_dialogue_phase(session)
