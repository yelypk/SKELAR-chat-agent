from __future__ import annotations

from dataclasses import dataclass

from agents.customer import CustomerAgent
from agents.judge import JudgeAgent
from agents.support import SupportAgent
from langchain_core.embeddings import Embeddings

from engine.config import AppConfig
from engine.runner import AgentBundle, RuntimeBundle, run_dialogue
from engine.session import DialogueSession


@dataclass(frozen=True)
class DialogueApp:
    agents: AgentBundle
    runtime: RuntimeBundle

    def invoke(self, session: DialogueSession) -> DialogueSession:
        return run_dialogue(session, self.agents, self.runtime)


def build_dialogue_app(
    config: AppConfig,
    embeddings: Embeddings,
    support_agent: SupportAgent,
    customer_agent: CustomerAgent,
    judge_agent: JudgeAgent,
) -> DialogueApp:
    return DialogueApp(
        agents=AgentBundle(
            support=support_agent,
            customer=customer_agent,
            judge=judge_agent,
        ),
        runtime=RuntimeBundle(
            config=config,
            embeddings=embeddings,
        ),
    )
