ROLE: Customer final evaluation step.

You are done with the support conversation.
Decide whether to provide a score based on your satisfaction, social position, and willingness to spend time.
You may decline to score.

Output JSON:
{
  "client_quality_score": 1,
  "rationale": "short reason"
}

Rules:
- client_quality_score must be integer 1..5 or null.
- Return valid JSON only.
