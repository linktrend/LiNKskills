# usage

## Capability Summary
Langfuse observability tool for LiNKskills. Logs ltr execution telemetry (action, latency, success) using vault-managed Langfuse credentials with silent-fail local mode.

## Commands
- `log`
  - Writes one execution event to Langfuse with service/action/latency/success fields.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/usage log --service gmail --action gmail.send --latency-ms 420 --success true`

## Resilience
- Uses vault keys: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, optional `LANGFUSE_HOST`.
- Defaults host to `https://cloud.langfuse.com` when host key is unavailable.
- If required keys are missing, prints `[UsageTracker] Disconnected: Running in local-only mode.` and continues without raising.
