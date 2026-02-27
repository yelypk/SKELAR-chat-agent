# SKELAR-chat-agent

Synthetic support dialogue simulator for evaluation data generation.

This repository contains:

- **Intent cards**: domain support knowledge in `scenarios/intents/`
- **Prompts**: role instructions for LLM calls in `prompts/`
- **Infrastructure**: Docker Compose for Postgres + Redis

Ollama is expected to run locally on the Windows host.

## Quickstart

### 1) Start infrastructure

```bash
docker compose up -d
```

Optional: Postgres with pgvector (different port to avoid conflicts):

```bash
docker compose --profile pgvector up -d
```

### 2) Configure environment

```bash
copy .env.example .env
```

### 3) Ollama (local on Windows)

Ensure Ollama is running locally (default `http://localhost:11434`) and pull a model:

```bash
ollama pull llama3.1
```

## Development docs

See `docs/DEVELOPMENT.md`.

## Repo structure

- `.cursor/rules/`: persistent Cursor rules (workflow, schema constraints, language policy)
- `scenarios/intents/`: intent cards (YAML)
- `prompts/`: LLM prompts (Markdown)
- `docs/`: development documentation
