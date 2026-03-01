from __future__ import annotations

import argparse
import json
import random
import uuid

from agents.providers import build_embeddings_client
from agents.customer import CustomerAgent
from agents.judge import JudgeAgent
from agents.support import SupportAgent
from dataset.db import DatasetWriter
from dataset.metrics import compute_balance_report
from engine.config import load_config
from engine.runner import AgentBundle, RuntimeBundle, run_dialogue
from engine.session import DialogueSession
from engine.state import TerminationReason
from scenarios.intent_loader import (
    build_customer_view,
    build_support_view,
    load_intents,
    sample_intent,
)
from scenarios.persona.generator import generate_persona_seed, generate_support_persona_seed


def _build_initial_session(
    run_id: str,
    seed: int,
    max_turns: int,
) -> DialogueSession:
    rng = random.Random(seed)
    intents = load_intents()
    intent = sample_intent(intents, rng)
    root_cause = rng.choice(intent.hidden_root_causes)
    persona, entropy_params = generate_persona_seed(rng)
    support_persona = generate_support_persona_seed(rng)

    planned_pool = intent.common_agent_mistakes.copy()
    rng.shuffle(planned_pool)
    planned_count = min(2, len(planned_pool))
    planned_mistakes = planned_pool[:planned_count]
    return DialogueSession(
        run_id=run_id,
        dialogue_id=str(uuid.uuid4()),
        seed=seed,
        turn_index=0,
        max_turns=max_turns,
        intent=intent,
        support_view=build_support_view(intent),
        customer_view=build_customer_view(intent, root_cause),
        root_cause=root_cause,
        persona=persona,
        support_persona=support_persona,
        dialogue_phase="greeting",
        entropy_params=entropy_params,
        planned_mistakes=planned_mistakes,
        observed_mistakes=[],
    )


def run_dialogues(num_dialogues: int, seed: int, print_report: bool = False) -> None:
    config = load_config()
    support = SupportAgent(config)
    customer = CustomerAgent(config)
    judge = JudgeAgent(config)
    agents = AgentBundle(support=support, customer=customer, judge=judge)
    runtime = RuntimeBundle(
        config=config,
        embeddings=build_embeddings_client(config),
    )
    writer = DatasetWriter(config.postgres_dsn)
    run_id = str(uuid.uuid4())

    for idx in range(num_dialogues):
        session = _build_initial_session(
            run_id=run_id,
            seed=seed + idx,
            max_turns=config.max_turns,
        )
        final_session = run_dialogue(session, agents, runtime)
        termination_reason = (
            final_session.termination_reason or TerminationReason.MAX_TURNS.value
        )
        if final_session.judge_output is None or final_session.judge_validation is None:
            raise RuntimeError("Runner must produce judge output and validation.")
        dialogue_id = writer.write_dialogue(
            {
                "dialogue_id": final_session.dialogue_id,
                "run_id": run_id,
                "intent_id": final_session.intent.intent_id,
                "hidden_root_cause": final_session.root_cause,
                "chaos_level": final_session.persona.chaos_level,
                "support_seniority": final_session.support_persona.seniority,
                "entropy_params": final_session.entropy_params,
                "planned_mistakes": final_session.planned_mistakes,
                "observed_mistakes": final_session.observed_mistakes,
                "resolved_gt": final_session.resolved,
                "termination_reason_gt": termination_reason,
                "client_quality_score": final_session.client_quality_score,
                "transcript_json": final_session.transcript_payload(),
            }
        )
        writer.write_judge(
            dialogue_id=dialogue_id,
            judge_output=final_session.judge_output,
            validation=final_session.judge_validation,
        )
        print(
            f"[{idx + 1}/{num_dialogues}] "
            f"intent={final_session.intent.intent_id} termination={termination_reason}"
        )

    if print_report:
        report = compute_balance_report(config.postgres_dsn, run_id=run_id)
        print("=== DATASET BALANCE REPORT ===")
        print(json.dumps(report, indent=2, ensure_ascii=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synthetic adversarial support dialogue simulator."
    )
    parser.add_argument("--num-dialogues", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report-balance", action="store_true")
    args = parser.parse_args()
    run_dialogues(
        num_dialogues=args.num_dialogues,
        seed=args.seed,
        print_report=args.report_balance,
    )


if __name__ == "__main__":
    main()
