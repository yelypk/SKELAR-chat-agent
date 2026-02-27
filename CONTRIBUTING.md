# Contributing

## Language policy

- Chat with maintainers: Ukrainian
- Repository artifacts: English (docs, prompts, intent cards, code comments/docstrings, commit messages)

## Development workflow

### Pre-commit hooks

Install pre-commit and enable hooks:

```bash
python -m pip install -U pre-commit
pre-commit install
```

Run hooks manually:

```bash
pre-commit run --all-files
```

### Infrastructure

Start Postgres + Redis with Docker:

```bash
docker compose up -d
```

Optional: Postgres with pgvector:

```bash
docker compose --profile pgvector up -d
```

## Adding / updating intent cards

Intent cards live in `scenarios/intents/` as YAML.

Please keep:

- Stable field names and types
- No prompt text inside intent cards
- `hidden_root_causes` must never be shown to the support agent simulator

If you add a new intent, run `pre-commit` locally and ensure CI passes.

