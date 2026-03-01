from __future__ import annotations

from langchain_core.embeddings import Embeddings

from engine.rules.deadlock import detect_deadlock as detect_deadlock_rule
from engine.rules.resolution import is_resolved as is_resolved_rule
from engine.rules.termination import compute_termination as compute_termination_rule
from engine.session import DialogueSession
from engine.state import DialogueState


def detect_deadlock(
    state: DialogueState,
    embeddings: Embeddings,
    window: int,
    threshold: float,
) -> bool:
    session = DialogueSession.from_state(state)
    return detect_deadlock_rule(session, embeddings, window, threshold)


def compute_termination(state: DialogueState) -> str | None:
    session = DialogueSession.from_state(state)
    return compute_termination_rule(session)


def apply_stop_conditions(
    state: DialogueState,
    embeddings: Embeddings,
    deadlock_window: int,
    deadlock_threshold: float,
) -> None:
    session = DialogueSession.from_state(state)
    session.resolved = is_resolved_rule(session, embeddings)
    session.max_turns_reached = session.turn_index >= session.max_turns
    session.deadlock_detected = detect_deadlock_rule(
        session=session,
        embeddings=embeddings,
        window=deadlock_window,
        threshold=deadlock_threshold,
    )
    session.termination_reason = compute_termination_rule(session)
    state.update(session.to_state())
