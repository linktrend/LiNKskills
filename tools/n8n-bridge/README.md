# n8n-bridge

## Capability Summary
Webhook trigger bridge for local n8n workflows.

Uses `n8n trigger` for deterministic workflow execution.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/n8n-bridge trigger --workflow 123 --payload '{"lead_id":"abc"}' --json`
- `bin/n8n-bridge trigger --workflow 123 --payload-file ./payload.json --json`

## Notes
- n8n credentials are resolved by `tools/n8n` via vault keys `N8N_BASE_URL` and `N8N_API_KEY`.
