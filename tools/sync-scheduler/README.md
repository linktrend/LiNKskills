# sync-scheduler

## Capability Summary
Calendar assistant wrapper that uses `gws` calendar operations to find and suggest Project Review slots with deterministic JSON output for agent workflows.

## CLI
- `--help`
- `--version`
- `--json`

## Notes
- Uses `gws` as the primary calendar interface.
- If `gws` event retrieval fails, returns a deterministic JSON error payload.

## Usage
- `bin/sync-scheduler suggest --date 2026-03-21 --duration-minutes 45 --count 3 --json`
