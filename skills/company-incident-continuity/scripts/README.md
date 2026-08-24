# Incident and continuity helper

`helper_tool.py` reads a JSON request from stdin or `--input` and emits one
deterministic review. It performs no network calls, connector calls, credential
access, deployment, rollback, isolation, communication sending, scheduling, or
state mutation.

Use `references/schemas.json` and `references/eval-suite.json` for the input,
output, and maintained evaluation contracts.
