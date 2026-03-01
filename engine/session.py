from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from engine.state import (
    DialogueState,
    IntentCard,
    JudgeValidationData,
    PersonaSeed,
    SupportPersonaSeed,
    SupportView,
)

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


@dataclass
class TurnRecord:
    speaker: Literal["support", "customer"]
    utterance: str
    payload: dict[str, Any]


@dataclass
class ConfusionEvent:
    turn_index: int
    type: str
    utterance: str


@dataclass
class DialogueSession:
    run_id: str
    dialogue_id: str
    seed: int
    turn_index: int
    max_turns: int
    intent: IntentCard
    support_view: SupportView
    customer_view: dict[str, Any]
    root_cause: str
    persona: PersonaSeed
    support_persona: SupportPersonaSeed
    dialogue_phase: Literal["greeting", "diagnosis", "resolution_check", "closure"]
    entropy_params: dict[str, Any]
    planned_mistakes: list[str]
    observed_mistakes: list[str]
    turns: list[TurnRecord] = field(default_factory=list)
    asked_questions: list[str] = field(default_factory=list)
    support_proposed_actions: list[str] = field(default_factory=list)
    customer_confusion_events: list[ConfusionEvent] = field(default_factory=list)
    patience: int = 0
    trust: int = 0
    resolved: bool = False
    escalated: bool = False
    customer_quit: bool = False
    agent_quit: bool = False
    deadlock_detected: bool = False
    max_turns_reached: bool = False
    termination_reason: str | None = None
    client_quality_score: int | None = None
    judge_output: dict[str, Any] | None = None
    judge_validation: JudgeValidationData | None = None
    resolution_path_vectors: list[list[float]] | None = None

    @property
    def is_terminal(self) -> bool:
        return self.termination_reason is not None

    @property
    def support_turn_count(self) -> int:
        return len([turn for turn in self.turns if turn.speaker == "support"])

    def transcript_payload(self) -> list[dict[str, Any]]:
        return [
            {
                "speaker": turn.speaker,
                "utterance": turn.utterance,
                "payload": turn.payload,
            }
            for turn in self.turns
        ]

    def confusion_events_payload(self, limit: int | None = None) -> list[dict[str, Any]]:
        events = self.customer_confusion_events[-limit:] if limit else self.customer_confusion_events
        return [
            {
                "turn_index": event.turn_index,
                "type": event.type,
                "utterance": event.utterance,
            }
            for event in events
        ]

    def ensure_resolution_path_vectors(self, embeddings: "Embeddings") -> list[list[float]]:
        if self.resolution_path_vectors is None:
            self.resolution_path_vectors = embeddings.embed_documents(self.intent.resolution_paths)
        return self.resolution_path_vectors

    @classmethod
    def from_state(cls, state: DialogueState) -> "DialogueSession":
        turns = [
            TurnRecord(
                speaker=turn["speaker"],
                utterance=turn["utterance"],
                payload=deepcopy(turn.get("payload", {})),
            )
            for turn in state["turns"]
        ]
        confusion_events = [
            ConfusionEvent(
                turn_index=int(event.get("turn_index", 0)),
                type=str(event.get("type", "none")),
                utterance=str(event.get("utterance", "")),
            )
            for event in state["customer_confusion_events"]
        ]
        return cls(
            run_id=state["run_id"],
            dialogue_id=state["dialogue_id"],
            seed=state["seed"],
            turn_index=state["turn_index"],
            max_turns=state["max_turns"],
            intent=state["intent"],
            support_view=deepcopy(state["support_view"]),
            customer_view=deepcopy(state["customer_view"]),
            root_cause=state["root_cause"],
            persona=state["persona"],
            support_persona=state["support_persona"],
            dialogue_phase=state["dialogue_phase"],
            entropy_params=deepcopy(state["entropy_params"]),
            planned_mistakes=list(state["planned_mistakes"]),
            observed_mistakes=list(state["observed_mistakes"]),
            turns=turns,
            asked_questions=list(state["asked_questions"]),
            support_proposed_actions=list(state["support_proposed_actions"]),
            customer_confusion_events=confusion_events,
            patience=state["patience"],
            trust=state["trust"],
            resolved=state["resolved"],
            escalated=state["escalated"],
            customer_quit=state["customer_quit"],
            agent_quit=state["agent_quit"],
            deadlock_detected=state["deadlock_detected"],
            max_turns_reached=state["max_turns_reached"],
            termination_reason=state.get("termination_reason"),
            client_quality_score=state.get("client_quality_score"),
            judge_output=deepcopy(state.get("judge_output")),
            judge_validation=deepcopy(state.get("judge_validation")),
            resolution_path_vectors=None,
        )

    def to_state(self) -> DialogueState:
        state: DialogueState = {
            "run_id": self.run_id,
            "dialogue_id": self.dialogue_id,
            "seed": self.seed,
            "turn_index": self.turn_index,
            "max_turns": self.max_turns,
            "intent": self.intent,
            "support_view": deepcopy(self.support_view),
            "customer_view": deepcopy(self.customer_view),
            "root_cause": self.root_cause,
            "persona": self.persona,
            "support_persona": self.support_persona,
            "dialogue_phase": self.dialogue_phase,
            "entropy_params": deepcopy(self.entropy_params),
            "planned_mistakes": list(self.planned_mistakes),
            "observed_mistakes": list(self.observed_mistakes),
            "turns": [
                {
                    "speaker": turn.speaker,
                    "utterance": turn.utterance,
                    "payload": deepcopy(turn.payload),
                }
                for turn in self.turns
            ],
            "asked_questions": list(self.asked_questions),
            "support_proposed_actions": list(self.support_proposed_actions),
            "customer_confusion_events": [
                {
                    "turn_index": event.turn_index,
                    "type": event.type,
                    "utterance": event.utterance,
                }
                for event in self.customer_confusion_events
            ],
            "patience": self.patience,
            "trust": self.trust,
            "resolved": self.resolved,
            "escalated": self.escalated,
            "customer_quit": self.customer_quit,
            "agent_quit": self.agent_quit,
            "deadlock_detected": self.deadlock_detected,
            "max_turns_reached": self.max_turns_reached,
            "termination_reason": self.termination_reason,
            "client_quality_score": self.client_quality_score,
        }
        if self.judge_output is not None:
            state["judge_output"] = deepcopy(self.judge_output)
        if self.judge_validation is not None:
            state["judge_validation"] = deepcopy(self.judge_validation)
        return state
