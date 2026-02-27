## Development (Windows)

This project generates synthetic support dialogues. Docker is used for infrastructure (Postgres + Redis). Ollama runs locally on the host machine (Windows).

### Prerequisites

- Python 3.12 (for CI parity)
- Docker Desktop
- Ollama for Windows

### Local setup

Create and activate a virtual environment, then install dependencies (files will be added in the repo):

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -U pip
pip install -r requirements-dev.txt
```

Create an environment file:

```bash
copy .env.example .env
```

### Start infrastructure (Docker)

Start Redis + Postgres:

```bash
docker compose up -d
```

Optional: start Postgres with pgvector (uses a different local port to avoid conflicts):

```bash
docker compose --profile pgvector up -d
```

### Ollama (local, not Docker)

1. Install Ollama on Windows.
2. Ensure the local server is running (default: `http://localhost:11434`).
3. Pull a model (example):

```bash
ollama pull llama3.1
```

### Running the project

The repository will include a minimal runnable demo entrypoint (to be added) that:

- loads an intent card from `scenarios/intents/`
- runs a deterministic dialogue loop (agent ↔ customer) with stop conditions
- runs the judge
- writes a dataset entry to `DATASET_OUTPUT_DIR`

Once added, it will be runnable via a `python -m ...` command documented in `README.md`.

