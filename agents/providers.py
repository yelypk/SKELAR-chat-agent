from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings

from engine.config import AppConfig

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:  # pragma: no cover - optional dependency for OpenAI provider
    ChatOpenAI = None
    OpenAIEmbeddings = None


def build_chat_client(config: AppConfig, model: str) -> BaseChatModel:
    if config.llm_provider == "openai":
        if ChatOpenAI is None:
            raise RuntimeError(
                "OpenAI provider requires 'langchain-openai'. Install dependencies from requirements-dev.txt."
            )
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=model,
            temperature=0,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            timeout=config.llm_timeout_seconds,
        )
    return ChatOllama(
        base_url=config.ollama_base_url,
        model=model,
        temperature=0,
        top_p=1,
        client_kwargs={"timeout": config.llm_timeout_seconds},
    )


def build_embeddings_client(config: AppConfig) -> Embeddings:
    if config.llm_provider == "openai":
        if OpenAIEmbeddings is None:
            raise RuntimeError(
                "OpenAI provider requires 'langchain-openai'. Install dependencies from requirements-dev.txt."
            )
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIEmbeddings(
            model=config.embedding_model,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            timeout=config.llm_timeout_seconds,
        )
    return OllamaEmbeddings(
        base_url=config.ollama_base_url,
        model=config.embedding_model,
        client_kwargs={"timeout": config.llm_timeout_seconds},
    )
