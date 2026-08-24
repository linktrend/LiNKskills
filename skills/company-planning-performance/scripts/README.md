# Company planning helper

`helper_tool.py` reads a JSON request from stdin or `--input` and emits one
deterministic JSON review. It performs no network calls, connector calls,
credential access, scheduling, Program mutation, Task creation, or file writes.

Example:

```bash
python3 skills/company-planning-performance/scripts/helper_tool.py --input request.json
```

Use `references/schemas.json` for the input/output contracts and
`references/eval-suite.json` for the maintained evaluation cases.
