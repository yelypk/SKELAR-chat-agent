from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    llm_provider: str
    ollama_base_url: str
    openai_base_url: str | None
    openai_api_key: str | None
    support_model: str
    customer_model: str
    judge_model: str
    embedding_model: str
    postgres_dsn: str
    max_turns: int
    deadlock_window: int
    deadlock_similarity_threshold: float
    retries_per_llm_call: int
    llm_timeout_seconds: int


def load_config() -> AppConfig:
    load_dotenv()
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if llm_provider not in {"ollama", "openai"}:
        raise ValueError("LLM_PROVIDER must be either 'ollama' or 'openai'")

    default_chat_model = "gpt-4o-mini" if llm_provider == "openai" else "qwen3:30b-thinking"
    default_embedding_model = (
        "text-embedding-3-small" if llm_provider == "openai" else "nomic-embed-text"
    )

    return AppConfig(
        llm_provider=llm_provider,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        support_model=os.getenv("SUPPORT_MODEL", default_chat_model),
        customer_model=os.getenv("CUSTOMER_MODEL", default_chat_model),
        judge_model=os.getenv("JUDGE_MODEL", default_chat_model),
        embedding_model=os.getenv("EMBEDDING_MODEL", default_embedding_model),
        postgres_dsn=os.getenv(
            "POSTGRES_DSN", "postgresql+psycopg://app:app@localhost:5432/skelar_chat_agent"
        ),
        max_turns=int(os.getenv("MAX_TURNS", "12")),
        deadlock_window=int(os.getenv("DEADLOCK_WINDOW", "3")),
        deadlock_similarity_threshold=float(
            os.getenv("DEADLOCK_SIMILARITY_THRESHOLD", "0.92")
        ),
        retries_per_llm_call=int(os.getenv("RETRIES_PER_LLM_CALL", "2")),
        llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "180")),
    )
