# Internal Script Utilities

## Guidelines
- **Black Box Principle**: The agent should run these scripts with `--help` to understand parameters rather than reading the source code.
- **Pathing**: Always use relative paths from the skill root or absolute paths from repository root.

## Available Scripts
- `initialize_folders.py`: Creates the standard folder structure (advanced/, examples/, references/, scripts/, .workdir/tasks/) for a new skill. Use with `--skill-path` parameter.
- `helper_tool.py`: Generic transformation helper for deterministic JSON output during design/migration workflows.
- Root scripts:
  - `../../validator.py`: Structural and contract compliance checks.
  - `../../global_evaluator.py`: Cross-skill health analytics from execution ledger data.
