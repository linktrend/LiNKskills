# ad-intel

## Capability Summary
Ad performance monitor for Marketing Strategist workflows.
Uses the `ltr` bridge for ad-related retrieval and tracks Spend vs. CTR to detect anomalies across Meta/Google campaigns.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/ad-intel monitor --bridge-command "ltr news search 'meta ads benchmark ctr' --json" --json`

## Notes
- Preferred path is using `ltr`-sourced metrics.
