# asset-filer

## Capability Summary
Asset ingestion bridge for creative outputs.
Routes `ltr asset upload [file]` to storage and records metadata in `lsl_memory.assets` for retrieval.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/asset-filer upload ./outputs/thumbnail.png --json`
- `bin/asset-filer upload ./outputs/script.md --asset-type script --project-id launch-q2 --json`

## Notes
- Uses `ltr` as the transport layer.
- Returns deterministic JSON output including upload path and registration status.
