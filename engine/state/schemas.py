from __future__ import annotations

from enum import Enum
from typing import Any, Literal, NotRequired, TypedDict

from pydantic import BaseModel, Field, field_validator


MISTAKE_WHITELIST = {
    "ignored_question",
    "incorrect_info",
    "rude_tone",
    "no_resolution",
    "unnecessary_escalation",
}


class TerminationReason(str, Enum):
    RESOLVED = "resolved"
    MAX_TURNS = "max_turns"
    DEADLOCK = "deadlock"
    ESCALATION = "escalation"
    CUSTOMER_QUIT = "customer_quit"
    AGENT_QUIT = "agent_quit"
    LLM_INVALID_JSON = "llm_invalid_json"


class SupportTurn(BaseModel):
    intent_hypothesis: str
    questions: list[str] = Field(default_factory=list)
    proposed_action: str
    used_manual_facts: list[str] = Field(default_factory=list)
    mistake_applied: Literal[
        "none",
        "ignored_question",
        "incorrect_info",
        "rude_tone",
        "no_resolution",
        "unnecessary_escalation",
    ]
    should_end: bool = False
    should_escalate: bool = False
    utterance: str


class CustomerTurn(BaseModel):
    thought_summary: str
    revealed_info: list[str] = Field(default_factory=list)
    emotional_shift: Literal["none", "more_frustrated", "calmer"]
    data_confusion: Literal[
        "none",
        "unclear_data_request",
        "unknown_data_location",
        "partial_or_incorrect_data",
    ] = "none"
    patience_delta: int = 0
    trust_delta: int = 0
    should_quit: bool = False
    utterance: str

    @field_validator("patience_delta", "trust_delta")
    @classmethod
    def _clamp_delta(cls, value: int) -> int:
        return max(-2, min(2, value))


class JudgeOutput(BaseModel):
    resolved: bool
    satisfaction: Literal["satisfied", "neutral", "unsatisfied"]
    quality_score: int
    agent_mistakes: list[str] = Field(default_factory=list)
    termination_reason: Literal[
        "resolved",
        "max_turns",
        "deadlock",
        "escalation",
        "customer_quit",
        "agent_quit",
        "llm_invalid_json",
    ]
    rationale: str

    @field_validator("quality_score")
    @classmethod
    def _quality_range(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("quality_score must be in range 1..5")
        return value

    @field_validator("agent_mistakes")
    @classmethod
    def _mistakes_in_vocab(cls, mistakes: list[str]) -> list[str]:
        invalid = [m for m in mistakes if m not in MISTAKE_WHITELIST]
        if invalid:
            raise ValueError(f"Unknown mistakes: {invalid}")
        return mistakes


class CustomerRatingOutput(BaseModel):
    client_quality_score: int | None = None
    rationale: str

    @field_validator("client_quality_score")
    @classmethod
    def _score_range(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 1 or value > 5:
            raise ValueError("client_quality_score must be in range 1..5")
        return value


class PersonaSeed(BaseModel):
    gender: str
    generation: str
    social_status: str
    education: str
    mbti_seed: str
    emotional_state: str
    impulsiveness: str
    volatility_trust: str
    communication_noise: str
    chaos_level: Literal["low", "medium", "high"]
    persona_seed_prompt: str


class SupportPersonaSeed(BaseModel):
    gender: str
    generation: str
    education: str
    communication_style: str
    seniority: Literal["junior", "middle", "senior", "lead"]
    support_persona_seed_prompt: str


class IntentCard(BaseModel):
    intent_id: str
    title: str
    description: str
    symptoms: list[str]
    hidden_root_causes: list[str]
    required_questions: list[str]
    resolution_paths: list[str]
    forbidden_actions: list[str]
    escalation_rules: list[str]
    common_agent_mistakes: list[str]

    @field_validator("common_agent_mistakes")
    @classmethod
    def _validate_vocab(cls, mistakes: list[str]) -> list[str]:
        invalid = [m for m in mistakes if m not in MISTAKE_WHITELIST]
        if invalid:
            raise ValueError(f"Intent contains unknown mistakes: {invalid}")
        return mistakes


class TurnRecord(TypedDict):
    speaker: Literal["support", "customer"]
    utterance: str
    payload: dict[str, Any]


class DialogueState(TypedDict):
    run_id: str
    dialogue_id: str
    seed: int
    turn_index: int
    max_turns: int
    intent: IntentCard
    support_view: dict[str, Any]
    customer_view: dict[str, Any]
    root_cause: str
    persona: PersonaSeed
    support_persona: SupportPersonaSeed
    dialogue_phase: Literal["greeting", "diagnosis", "resolution_check", "closure"]
    entropy_params: dict[str, Any]
    planned_mistakes: list[str]
    observed_mistakes: list[str]
    turns: list[TurnRecord]
    asked_questions: list[str]
    support_proposed_actions: list[str]
    customer_confusion_events: list[dict[str, Any]]
    patience: int
    trust: int
    resolved: bool
    escalated: bool
    customer_quit: bool
    agent_quit: bool
    deadlock_detected: bool
    max_turns_reached: bool
    termination_reason: NotRequired[str | None]
    client_quality_score: NotRequired[int | None]
    judge_output: NotRequired[dict[str, Any]]
    judge_validation: NotRequired[dict[str, Any]]
