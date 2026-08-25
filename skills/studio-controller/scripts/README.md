# Internal Script Utilities

`helper_tool.py` returns deterministic review summaries from JSON input. It is
offline-only and cannot reach Odoo, a connector, a ledger, or a source system.
Run it with `--help`; use paths relative to the skill root.

The root validator is run from the repository root:
`python3 validator.py --repo-root . --path skills/studio-controller`.
