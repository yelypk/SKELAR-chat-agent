from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents.customer import CustomerAgent
from agents.judge import JudgeAgent
from agents.llm import InvalidLLMOutputError, build_embeddings_client
from agents.support import SupportAgent
from engine.config import AppConfig
from engine.orchestrator.escalation_policy import should_allow_escalation
from engine.orchestrator.judge_validation import validate_judge_output
from engine.orchestrator.mistake_detection import detect_observed_mistakes
from engine.orchestrator.stop_conditions import apply_stop_conditions
from engine.state import DialogueState


def _next_planned_mistake(state: DialogueState) -> str:
    idx = len([t for t in state["turns"] if t["speaker"] == "support"])
    if idx >= len(state["planned_mistakes"]):
        return "none"
    return state["planned_mistakes"][idx]


def _latest_support_questions(state: DialogueState) -> list[str]:
    for turn in reversed(state["turns"]):
        if turn["speaker"] == "support":
            payload = turn.get("payload", {})
            questions = payload.get("questions", [])
            if isinstance(questions, list):
                return [str(question) for question in questions]
            return []
    return []


def _update_dialogue_phase(state: DialogueState) -> None:
    support_turns = len([turn for turn in state["turns"] if turn["speaker"] == "support"])
    customer_turns = len([turn for turn in state["turns"] if turn["speaker"] == "customer"])
    if state.get("termination_reason") or state["resolved"] or state["escalated"]:
        state["dialogue_phase"] = "closure"
        return
    if state["customer_quit"] or state["agent_quit"]:
        state["dialogue_phase"] = "closure"
        return
    if support_turns == 0 or customer_turns == 0:
        state["dialogue_phase"] = "greeting"
        return
    latest_questions = _latest_support_questions(state)
    state["dialogue_phase"] = "diagnosis" if latest_questions else "resolution_check"


def build_dialogue_graph(
    config: AppConfig,
    support_agent: SupportAgent,
    customer_agent: CustomerAgent,
    judge_agent: JudgeAgent,
):
    embeddings = build_embeddings_client(config)

    def support_turn(state: DialogueState) -> DialogueState:
        if state.get("termination_reason"):
            return state
        payload = {
            "intent_card": state["support_view"],
            "support_persona_seed_prompt": state["support_persona"].support_persona_seed_prompt,
            "transcript": state["turns"],
            "planned_mistake": _next_planned_mistake(state),
            "dialogue_phase": state["dialogue_phase"],
            "customer_confusion_events": state["customer_confusion_events"][-3:],
            "patience": state["patience"],
            "trust": state["trust"],
        }
        try:
            output = support_agent.run_turn(payload)
        except InvalidLLMOutputError:
            state["termination_reason"] = "llm_invalid_json"
            return state
        state["turns"].append(
            {
                "speaker": "support",
                "utterance": output.utterance,
                "payload": output.model_dump(),
            }
        )
        state["turn_index"] += 1
        state["asked_questions"].extend(output.questions)
        state["support_proposed_actions"].append(output.proposed_action)
        # Ignore model-requested hard stop as a termination control input.
        # Stop logic must be governed by deterministic orchestrator conditions.
        if output.should_escalate and should_allow_escalation(state):
            state["escalated"] = True
        # Deterministic post-checks own observed mistakes, not model self-report.
        state["observed_mistakes"] = detect_observed_mistakes(state)
        return state

    def orchestrator_after_support(state: DialogueState) -> DialogueState:
        if state.get("termination_reason") == "llm_invalid_json":
            return state
        apply_stop_conditions(
            state=state,
            embeddings=embeddings,
            deadlock_window=config.deadlock_window,
            deadlock_threshold=config.deadlock_similarity_threshold,
        )
        state["observed_mistakes"] = detect_observed_mistakes(state)
        _update_dialogue_phase(state)
        return state

    def customer_turn(state: DialogueState) -> DialogueState:
        if state.get("termination_reason"):
            return state
        payload = {
            "intent": state["intent"].intent_id,
            "persona_seed_prompt": state["persona"].persona_seed_prompt,
            "customer_context": state["customer_view"],
            "transcript": state["turns"],
            "dialogue_phase": state["dialogue_phase"],
            "patience": state["patience"],
            "trust": state["trust"],
        }
        try:
            output = customer_agent.run_turn(payload)
        except InvalidLLMOutputError:
            state["termination_reason"] = "llm_invalid_json"
            return state
        state["turns"].append(
            {
                "speaker": "customer",
                "utterance": output.utterance,
                "payload": output.model_dump(),
            }
        )
        state["turn_index"] += 1
        state["patience"] += output.patience_delta
        state["trust"] += output.trust_delta
        if output.data_confusion != "none":
            state["customer_confusion_events"].append(
                {
                    "turn_index": state["turn_index"],
                    "type": output.data_confusion,
                    "utterance": output.utterance,
                }
            )
        if output.should_quit:
            state["customer_quit"] = True
        return state

    def orchestrator_after_customer(state: DialogueState) -> DialogueState:
        if state.get("termination_reason") == "llm_invalid_json":
            return state
        apply_stop_conditions(
            state=state,
            embeddings=embeddings,
            deadlock_window=config.deadlock_window,
            deadlock_threshold=config.deadlock_similarity_threshold,
        )
        state["observed_mistakes"] = detect_observed_mistakes(state)
        _update_dialogue_phase(state)
        return state

    def customer_rating(state: DialogueState) -> DialogueState:
        payload = {
            "intent": state["intent"].intent_id,
            "persona_seed_prompt": state["persona"].persona_seed_prompt,
            "termination_reason": state.get("termination_reason"),
            "transcript": state["turns"],
        }
        try:
            rating = customer_agent.rate_dialogue(payload)
            state["client_quality_score"] = rating.client_quality_score
        except InvalidLLMOutputError:
            state["client_quality_score"] = None
        return state

    def judge_turn(state: DialogueState) -> DialogueState:
        payload = {
            "intent": state["intent"].intent_id,
            "client_quality_score": state.get("client_quality_score"),
            "transcript": state["turns"],
        }
        try:
            judge_output = judge_agent.evaluate(payload).model_dump()
        except InvalidLLMOutputError:
            judge_output = {
                "resolved": False,
                "satisfaction": "unsatisfied",
                "quality_score": 1,
                "agent_mistakes": [],
                "termination_reason": "llm_invalid_json",
                "rationale": "Judge failed to return valid JSON.",
            }
        state["judge_output"] = judge_output
        state["judge_validation"] = validate_judge_output(
            judge_output=judge_output,
            observed_mistakes=state["observed_mistakes"],
            resolved_gt=state["resolved"],
            termination_reason_gt=state.get("termination_reason", "llm_invalid_json"),
        )
        return state

    def route_after_support(state: DialogueState) -> str:
        return "customer_turn" if not state.get("termination_reason") else "customer_rating"

    def route_after_customer(state: DialogueState) -> str:
        return "support_turn" if not state.get("termination_reason") else "customer_rating"

    graph = StateGraph(DialogueState)
    graph.add_node("support_turn", support_turn)
    graph.add_node("orchestrator_after_support", orchestrator_after_support)
    graph.add_node("customer_turn", customer_turn)
    graph.add_node("orchestrator_after_customer", orchestrator_after_customer)
    graph.add_node("customer_rating", customer_rating)
    graph.add_node("judge_turn", judge_turn)
    # The customer starts the conversation and reveals the topic first.
    graph.set_entry_point("customer_turn")

    graph.add_edge("support_turn", "orchestrator_after_support")
    graph.add_conditional_edges(
        "orchestrator_after_support",
        route_after_support,
        {"customer_turn": "customer_turn", "customer_rating": "customer_rating"},
    )
    graph.add_edge("customer_turn", "orchestrator_after_customer")
    graph.add_conditional_edges(
        "orchestrator_after_customer",
        route_after_customer,
        {"support_turn": "support_turn", "customer_rating": "customer_rating"},
    )
    graph.add_edge("customer_rating", "judge_turn")
    graph.add_edge("judge_turn", END)
    return graph.compile()
