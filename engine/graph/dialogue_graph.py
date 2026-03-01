from __future__ import annotations

from agents.customer import CustomerAgent
from agents.judge import JudgeAgent
from agents.support import SupportAgent
from engine.config import AppConfig
from engine.runner import AgentBundle, run_dialogue
from engine.session import DialogueSession
from engine.state import DialogueState


class _RunnerApp:
    def __init__(
        self,
        config: AppConfig,
        support_agent: SupportAgent,
        customer_agent: CustomerAgent,
        judge_agent: JudgeAgent,
    ) -> None:
        self._config = config
        self._agents = AgentBundle(
            support=support_agent,
            customer=customer_agent,
            judge=judge_agent,
        )

    def invoke(self, state: DialogueState) -> DialogueState:
        session = DialogueSession.from_state(state)
        final_session = run_dialogue(session, self._agents, self._config)
        return final_session.to_state()


def build_dialogue_graph(
    config: AppConfig,
    support_agent: SupportAgent,
    customer_agent: CustomerAgent,
    judge_agent: JudgeAgent,
):
    return _RunnerApp(
        config=config,
        support_agent=support_agent,
        customer_agent=customer_agent,
        judge_agent=judge_agent,
    )
