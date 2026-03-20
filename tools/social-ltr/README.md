# social-ltr

## Capability Summary
Unified social wrapper that routes post and comment retrieval actions across YouTube, TikTok, and X through the `ltr` tool, returning deterministic JSON payloads.

## CLI
- `--help`
- `--version`
- `--json`

## Usage
- `bin/social-ltr post --provider youtube --target-id <comment_id> --text "Thanks for your feedback" --json`
- `bin/social-ltr fetch-comments --provider youtube --target-id <video_id> --json`
- `bin/social-ltr post --provider x --target-id <thread_id> --text "Launch update" --json`

## Routing
- YouTube operations map to `ltr youtube` comment commands.
- TikTok/X operations are passed through to `ltr social ...` provider routes.
