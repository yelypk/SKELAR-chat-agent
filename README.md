# SKELAR-chat-agent

Synthetic support dialogue simulator for evaluation data generation.

This repository contains:

- **Intent cards**: domain support knowledge in `scenarios/intents/`
- **Prompts**: role instructions for LLM calls in `prompts/`
- **Infrastructure**: Docker Compose for Postgres + Redis

LLM provider is configurable via `.env` (`ollama` or `openai`).

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

### 3) Choose LLM provider in `.env`

Set provider and models in `.env`:

- For **Ollama**:
  - `LLM_PROVIDER=ollama`
  - `OLLAMA_BASE_URL=http://localhost:11434`
  - `SUPPORT_MODEL=qwen3:30b-thinking`
  - `CUSTOMER_MODEL=qwen3:30b-thinking`
  - `JUDGE_MODEL=qwen3:30b-thinking`
  - `EMBEDDING_MODEL=nomic-embed-text`
  - `LLM_TIMEOUT_SECONDS=180`
- For **OpenAI**:
  - `LLM_PROVIDER=openai`
  - `OPENAI_API_KEY=<your_api_key>`
  - `OPENAI_BASE_URL=` (optional)
  - `SUPPORT_MODEL=gpt-4o-mini`
  - `CUSTOMER_MODEL=gpt-4o-mini`
  - `JUDGE_MODEL=gpt-4o-mini`
  - `EMBEDDING_MODEL=text-embedding-3-small`
  - `LLM_TIMEOUT_SECONDS=180`

For external DB tools (for example TablePlus), use:
- `postgresql://app:app@localhost:5432/skelar_chat_agent`

If you use Ollama, ensure it is running locally and pull required models:

```bash
ollama pull qwen3:30b-thinking
ollama pull nomic-embed-text
```

### 4) Install Python dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements-dev.txt
```

### 5) Run simulator

```bash
python -m engine.run --num-dialogues 3 --seed 42
```

This command runs deterministic self-play sessions and writes:
- dialogue labels in table `dialogues`
- judge outputs in table `judge_evaluations`
- judge checks in table `judge_validations`

Optional balance report for the generated run:

```bash
python -m engine.run --num-dialogues 20 --seed 42 --report-balance
```

### 6) Apply database migrations (Alembic)

Use Alembic instead of relying only on runtime `create_all`:

```bash
alembic upgrade head
```

### 7) Export judge CSV datasets (`generate.py` and `analyze.py`)

Two root scripts prepare dedicated CSV files for judge training and evaluation.

`generate.py` creates the judge-visible training dataset:

```bash
python generate.py --after-dialogue-id c3fb87a8-28f5-4769-81b8-b84a64634a12
```

Output file:
- `dataset_outputs/judge_training_dataset.csv`

Columns (only data visible to judge):
- `intent`
- `client_quality_score`
- `transcript`

`analyze.py` creates judge outputs + judge performance evaluation for the same filtered dialogue slice:

```bash
python analyze.py --after-dialogue-id c3fb87a8-28f5-4769-81b8-b84a64634a12
```

Output file:
- `dataset_outputs/judge_results_and_eval.csv`

Columns:
- `dialogue_id`, `resolved`, `satisfaction`, `quality_score`, `agent_mistakes`, `termination_reason`, `rationale`
- `resolved_match`, `termination_match`, `validated_mistakes`, `precision`, `recall`, `validation_notes`

Both scripts apply the same filters:
- dialogues strictly after provided `dialogue_id` (ordered by `created_at`, then `id`)
- exclude rows where `termination_reason_gt = max_turns`

Optional arguments for both scripts:
- `--dsn` to override DB connection string
- `--output-csv` to override output file path

## Development docs

See:

- `docs/DEVELOPMENT.md`
- `docs/INTENT_CARDS.md`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/MODULE_IO.md`

## Repo structure

- `.cursor/rules/`: persistent Cursor rules (workflow, schema constraints, language policy)
- `scenarios/intents/`: intent cards (YAML)
- `scenarios/persona/`: on-the-fly persona seed generator for chaos mode
- `prompts/`: LLM prompts (Markdown)
- `engine/`: LangGraph loop, state, and deterministic stop-condition orchestrator
- `agents/`: role wrappers (customer, support, judge)
- `dataset/`: Postgres persistence layer
- `docs/`: development documentation
