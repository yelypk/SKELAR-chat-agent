## Intent cards

Intent cards are the canonical source of support knowledge. They must be deterministic, structured, and machine-validated.

### Location

All intent cards live in `scenarios/intents/` as YAML files.

### Required fields

Each intent card MUST include:

- `intent_id` (string, unique)
- `title` (string)
- `description` (string, 1–2 sentences)
- `symptoms` (list of strings)
- `hidden_root_causes` (list of strings; never shown to support agent)
- `required_questions` (list of strings)
- `resolution_paths` (list of strings)
- `forbidden_actions` (list of strings)
- `escalation_rules` (list of strings)
- `common_agent_mistakes` (list of strings; controlled vocabulary)

### Constraints

- Do not encode dialogue control-flow inside intent cards.
- Do not include prompt text in intent cards.
- Keep phrasing concise and avoid repetitive wording across intents.

### Validation

CI runs `pre-commit` which includes YAML validation and `yamllint`.

