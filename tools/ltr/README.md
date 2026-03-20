# ltr

## Capability Summary
LiNKtrend Runtime gateway for non-Workspace Google services, non-Google services, and local security/runtime controls.

Workspace services (Gmail/Drive/Docs/Sheets/Calendar/Chat/Tasks/Slides/Forms) were moved to `gws`.

`ltr` current service lanes:
- Google non-Workspace: `analytics`, `search-console`, `ads`, `youtube`, `maps`
- Non-Google: `news`, `env`
- Local platform controls: `vault`, `sandbox`

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/ltr analytics report --property-id <id> --start-date 2026-01-01 --end-date 2026-01-31 --metrics activeUsers`
- `bin/ltr ads campaigns --customer-id <id>`
- `bin/ltr search-console sites`
- `bin/ltr youtube stats`
- `bin/ltr maps places-search --query "coworking taipei"`
- `bin/ltr news trending --limit 10`
- `bin/ltr env weather --lat 25.033 --lng 121.565`
- `bin/ltr vault set ltr.credentials.json ./credentials.json`
- `bin/ltr sandbox run "python3 -V"`
