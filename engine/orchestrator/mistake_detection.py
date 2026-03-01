from __future__ import annotations

from engine.rules.mistakes import detect_observed_mistakes as detect_session_mistakes
from engine.session import DialogueSession
from engine.state import DialogueState


def detect_observed_mistakes(state: DialogueState) -> list[str]:
    session = DialogueSession.from_state(state)
    return detect_session_mistakes(session)
