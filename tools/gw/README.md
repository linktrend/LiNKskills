# gw

## Capability Summary
Unified gateway for Google Workspace. Use for Gmail (send/list), Drive (upload/share), Docs (formatting/markdown), Sheets (logging), Calendar (scheduling), and Chat.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/gw gmail send --to user@example.com --subject "Hello" --body "Test message"`
- `bin/gw gmail list --limit 20`
- `bin/gw drive upload --path ./report.pdf --folder-id <folder_id>`
- `bin/gw drive share --file-id <file_id> --email user@example.com --role writer`
- `bin/gw docs append-markdown --doc-id <doc_id> --markdown "# Update"`
- `bin/gw sheets log --sheet-id <sheet_id> --range A1 --values "status,ok"`
- `bin/gw calendar schedule --title "Standup" --start "2026-02-23T09:00:00" --end "2026-02-23T09:30:00"`
- `bin/gw chat send --space <space_id> --text "Build complete"`
