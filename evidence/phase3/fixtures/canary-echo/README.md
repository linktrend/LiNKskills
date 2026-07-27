# Canary-echo eval suite (Phase 3)

Genuine packaged-tool execution canary for the Eval Runner certification path.

## Rules

- Cases must declare `execute` (`packaged_tool` or `command`).
- Suite-authored `observed_output` / `fixture_output` are **not** present and must never be treated as executed evidence.
- Certification requires sealed executor receipts binding case, skill release hash, tool hash, execution-profile hash, environment/toolchain, and collected evidence.

## Run

```bash
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m linkskills_eval_runner run evidence/phase3/fixtures/canary-echo/eval-suite.yaml -o evidence/phase3/canary-echo-cli.json
```

Evidence summary: `evidence/phase3/canary-echo-cli.txt`
