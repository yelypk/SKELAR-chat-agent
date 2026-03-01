# SKELAR Chat Agent

Synthetic support-dialogue simulator for generating evaluation-ready datasets.

## What it does
This project runs **self-play customer support conversations** between three roles:
- **Customer agent** - knows the hidden root cause and reveals details gradually.
- **Support agent** - tries to solve the issue using intent-card knowledge.
- **Judge agent** - scores the finished dialogue and compares its verdict to deterministic ground truth.

The result is a reproducible pipeline for generating:
- labeled support dialogues,
- judge evaluation outputs,
- CSV datasets for training or benchmarking evaluators.

## Why it is useful
Real support data is expensive, sensitive, and hard to label consistently. This project creates a controlled environment where dialogue flow is realistic enough for experimentation, while labels and stop conditions stay code-driven.

## Tech stack
- **Python**
- **Deterministic Python runner** orchestration
- **LangChain** model interfaces
- **PostgreSQL** for dialogue and evaluation storage
- **Redis** for local infrastructure
- **Ollama or OpenAI** as the LLM backend
- Optional **pgvector** profile for vector-enabled Postgres

## Quick start
```bash
# 1) Start local infrastructure
docker compose up -d

# 2) Create environment file
cp .env.example .env

# 3) Install dependencies
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements-dev.txt

# 4) Choose your provider in .env
# LLM_PROVIDER=ollama
# or
# LLM_PROVIDER=openai

# 5) Run a small batch
python -m engine.run --num-dialogues 3 --seed 42
```

## Outputs
A run writes data into Postgres and can later export CSV files for downstream evaluation workflows:

```bash
python generate.py --after-dialogue-id <existing-dialogue-uuid>
python analyze.py --after-dialogue-id <existing-dialogue-uuid>
```

## Hackathon demo flow
1. Start Docker services.
2. Configure one LLM provider.
3. Generate a few synthetic dialogues.
4. Export judge-facing CSVs.
5. Show how deterministic labels and judge outputs can be compared.

## Important notes
- `generate.py` and `analyze.py` require an **existing** `dialogue_id` as an anchor.
- The simulator is a **dataset-generation system**, not a production support bot.
- If you use the `pgvector` Docker profile, update the DSN to the vector-enabled Postgres port.

## Project structure
```text
agents/      role-specific LLM wrappers
engine/      orchestration, session model, deterministic runner
scenarios/   support intents and persona generation
dataset/     database persistence and metrics
prompts/     role instructions
docs/        architecture and development notes
```

## One-line pitch
**A reproducible synthetic customer-support simulator that generates dialogues, judge scores, and evaluation datasets for LLM benchmarking.**
