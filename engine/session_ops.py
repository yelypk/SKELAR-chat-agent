from __future__ import annotations

from engine.session import ConfusionEvent, DialogueSession, TurnRecord
from engine.state import CustomerTurn, SupportTurn


def append_customer_turn(session: DialogueSession, output: CustomerTurn) -> None:
    session.turns.append(
        TurnRecord(
            speaker="customer",
            utterance=output.utterance,
            payload=output.model_dump(),
        )
    )
    session.turn_index += 1
    session.patience += output.patience_delta
    session.trust += output.trust_delta
    if output.data_confusion != "none":
        session.customer_confusion_events.append(
            ConfusionEvent(
                turn_index=session.turn_index,
                type=output.data_confusion,
                utterance=output.utterance,
            )
        )
def append_support_turn(session: DialogueSession, output: SupportTurn) -> None:
    session.turns.append(
        TurnRecord(
            speaker="support",
            utterance=output.utterance,
            payload=output.model_dump(),
        )
    )
    session.turn_index += 1
    session.asked_questions.extend(output.questions)
    session.support_proposed_actions.append(output.proposed_action)
def mark_escalated(session: DialogueSession) -> None:
    session.escalated = True


def mark_customer_quit(session: DialogueSession) -> None:
    session.customer_quit = True
