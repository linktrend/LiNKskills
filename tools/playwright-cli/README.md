# playwright-cli

## Capability Summary
Stateless Playwright command wrapper for browser setup and one-shot page automation tasks (`install`, `screenshot`, `pdf`, `codegen`). Use when an agent needs deterministic JSON outputs from Playwright CLI without maintaining an interactive session.

## Commands
- `install`
  - Downloads required Playwright browser binaries.
- `screenshot --url <URL> --path <PATH>`
  - Captures a page screenshot at the target path.
- `pdf --url <URL> --path <PATH>`
  - Exports a page PDF at the target path.
- `codegen --url <URL> [--path <PATH>]`
  - Starts Playwright code generation and writes output script for agent review.

## CLI
- `--help`
- `--version`
- `--json` (output is always deterministic JSON: `{"status":"...","output":"...","path":"..."}`)

## Usage
- `bin/pw-cli install`
- `bin/pw-cli screenshot --url https://example.com --path /tmp/example.png`
- `bin/pw-cli pdf --url https://example.com --path /tmp/example.pdf`
- `bin/pw-cli codegen --url https://example.com --path /tmp/codegen.ts`
