# Internal Script Utilities

## Guidelines
- **Black Box Principle**: The agent should run these scripts with `--help` to understand parameters rather than reading the source code.
- **Pathing**: Always use relative paths from the skill root.

## Available Scripts
- `helper_tool.py`: validates canary echo token / mode arguments and prints JSON.
- Root-level validator: run `python3 validator.py --path skills/canary-echo --repo-root .` from repository root.
