from __future__ import annotations

from engine.orchestrator.escalation_policy import should_allow_escalation
from engine.orchestrator.text_similarity import jaccard_similarity, normalize_tokens
from engine.state import DialogueState

FORBIDDEN_ACTION_SIM_THRESHOLD = 0.22
REQUIRED_QUESTION_SIM_THRESHOLD = 0.15
RUDE_MARKERS = frozenset(
    {
        "stupid",
        "dumb",
        "your fault",
        "nonsense",
        "can't you read",
        "stop wasting",
    }
)

def _contains_rude_tone(state: DialogueState) -> bool:
    for turn in state["turns"]:
        if turn["speaker"] != "support":
            continue
        text = turn["utterance"].casefold()
        if any(marker in text for marker in RUDE_MARKERS):
            return True
    return False


def _contains_forbidden_action(state: DialogueState) -> bool:
    forbidden = state["support_view"].get("forbidden_actions", [])
    if not forbidden:
        return False
    forbidden_tokens = [normalize_tokens(item) for item in forbidden]
    for action in state["support_proposed_actions"]:
        action_tokens = normalize_tokens(action)
        for rule_tokens in forbidden_tokens:
            if jaccard_similarity(action_tokens, rule_tokens) >= FORBIDDEN_ACTION_SIM_THRESHOLD:
                return True
    return False


def _ignored_required_questions(state: DialogueState) -> bool:
    required_questions = state["support_view"].get("required_questions", [])
    if not required_questions:
        return False

    asked_token_sets = [normalize_tokens(question) for question in state["asked_questions"]]
    asked_token_sets = [tokens for tokens in asked_token_sets if tokens]
    if not asked_token_sets:
        return True

    for question in required_questions:
        rule_tokens = normalize_tokens(question)
        best_similarity = max(
            (jaccard_similarity(rule_tokens, asked_tokens) for asked_tokens in asked_token_sets),
            default=0.0,
        )
        if best_similarity < REQUIRED_QUESTION_SIM_THRESHOLD:
            return True
    return False


def _support_attempted_escalation(state: DialogueState) -> bool:
    for turn in state["turns"]:
        if turn["speaker"] != "support":
            continue
        payload = turn.get("payload", {})
        if payload.get("should_escalate") is True:
            return True
    return False


def _unnecessary_escalation(state: DialogueState) -> bool:
    if not _support_attempted_escalation(state):
        return False
    return not should_allow_escalation(state)


def detect_observed_mistakes(state: DialogueState) -> list[str]:
    observed: list[str] = []
    if _ignored_required_questions(state):
        observed.append("ignored_question")
    if _contains_forbidden_action(state):
        observed.append("incorrect_info")
    if _contains_rude_tone(state):
        observed.append("rude_tone")
    if state.get("termination_reason") and state.get("termination_reason") != "resolved":
        observed.append("no_resolution")
    if _unnecessary_escalation(state):
        observed.append("unnecessary_escalation")
    return sorted(set(observed))
