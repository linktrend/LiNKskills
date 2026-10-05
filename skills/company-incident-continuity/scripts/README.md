# Incident and continuity helper

`helper_tool.py` reads a JSON request from stdin or `--input` and emits one
deterministic review. It performs no network calls, connector calls, credential
access, deployment, rollback, isolation, communication sending, scheduling, or
state mutation.

Use `references/schemas.json` and `references/eval-suite.json` for the input,
output, and maintained evaluation contracts.

The new bounded source-review helper branch uses the existing LiNKskills Python environment with `jsonschema`. If that dependency is unavailable, stop and report the runtime gap; do not install packages or access the network automatically. This source contract is not proof of a native consumer execution route.
