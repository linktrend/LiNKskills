# COMMAND_REFERENCE

Comprehensive command index for all executable tool wrappers under `tools/*/bin`.

## Global Flags
- `--help`: show command usage
- `--version`: show wrapper version when supported
- `--json`: structured machine-readable output when supported

## Runtime Routing Standard
- Workspace services: `gws`
- Non-Workspace Google + non-Google + local runtime controls: `ltr`
- Service ownership source of truth: `configs/service_ownership.json`

## `gws`
- Registry Path: `/tools/gws`
- Description: Pinned Google Workspace CLI wrapper sourced from `link-gws-cli` with strict checksum/version validation.
- Binaries: `gws`
- Usage Examples:
  - `tools/gws/bin/gws --version`
  - `tools/gws/bin/gws drive files list --params '{"pageSize": 5}'`
  - `tools/gws/bin/gws gmail +send --to user@example.com --subject "Hello" --body "Test"`
  - `tools/gws/bin/gws calendar +agenda --today`

## `ltr`
- Registry Path: `tools/ltr/src/cli.py`
- Description: LiNKtrend Runtime gateway for non-Workspace Google services, non-Google services, and local security/runtime controls.
- Binaries: `ltr`
- Usage Examples:
  - `tools/ltr/bin/ltr analytics report --property-id <id> --start-date 2026-01-01 --end-date 2026-01-31 --metrics activeUsers`
  - `tools/ltr/bin/ltr ads campaigns --customer-id <id>`
  - `tools/ltr/bin/ltr youtube stats`
  - `tools/ltr/bin/ltr news trending --limit 10`
  - `tools/ltr/bin/ltr vault set ltr.credentials.json ./credentials.json`
  - `tools/ltr/bin/ltr sandbox run "python3 -V"`

## `playwright-cli`
- Registry Path: `/tools/playwright-cli`
- Description: Stateless Playwright CLI wrapper for browser install and one-shot automation tasks with deterministic JSON outputs.
- Binaries: `pw-cli`
- Usage Examples:
  - `bin/pw-cli install`
  - `bin/pw-cli screenshot --url https://example.com --path /tmp/example.png`
  - `bin/pw-cli pdf --url https://example.com --path /tmp/example.pdf`
  - `bin/pw-cli codegen --url https://example.com --path /tmp/codegen.ts`

## `fast-playwright`
- Registry Path: `/tools/fast-playwright`
- Description: FastMCP Playwright server wrapper for interactive, session-based browser automation.
- Binaries: `start-mcp`
- Usage Examples: refer to the tool README

## `vault`
- Registry Path: `/tools/vault`
- Description: Encrypted credential vault using LSL_MASTER_KEY with audited set/get/list operations.
- Binaries: `vault`
- Usage Examples:
  - `bin/vault set google_credentials ./credentials.json`
  - `bin/vault get google_credentials`
  - `bin/vault list`

## `sandbox`
- Registry Path: `/tools/sandbox`
- Description: Ephemeral Docker runtime for isolated command execution with memory limits and default network isolation.
- Binaries: `sandbox-run`
- Usage Examples:
  - `bin/sandbox-run "python3 -V"`
  - `bin/sandbox-run --allow-network "pip index versions requests"`

## `usage`
- Registry Path: `/tools/usage`
- Description: Langfuse-based usage telemetry tool with silent local fallback, host defaulting, and vault-managed credentials.
- Binaries: `usage`
- Usage Examples:
  - `bin/usage log --service gmail --action gmail.send --latency-ms 420 --success true`

## `memory`
- Registry Path: `/tools/memory`
- Description: Supabase-backed memory tool with scoped recall plus Markdown notes in lsl_memory.notes.
- Binaries: `memory`
- Usage Examples:
  - `bin/memory remember --agent-id lisa --project-id growth --content "Launch postmortem: CTA underperformed."`
  - `bin/memory recall --agent-id lisa --project-id growth --query "postmortem" --limit 10`
  - `bin/memory add-note --agent-id lisa --title "Standup" --md-file ./standup.md`
  - `bin/memory get-note --agent-id lisa --title "Standup" --limit 10`

## `n8n`
- Registry Path: `/tools/n8n`
- Description: n8n workflow API tool for read, create, activate/deactivate, and trigger operations with vault-backed API keys.
- Binaries: `n8n`
- Usage Examples:
  - `bin/n8n list --limit 20`
  - `bin/n8n read --workflow-id 123`
  - `bin/n8n create --workflow-json '{"name":"Lead Router","nodes":[],"connections":{}}'`
  - `bin/n8n activate --workflow-id 123`
  - `bin/n8n trigger --workflow-id 123 --payload-json '{"lead_id":"abc"}'`

## `stripe`
- Registry Path: `/tools/stripe`
- Description: Stripe billing operations tool with vault-backed API key and invoice retrieval commands.
- Binaries: `stripe`
- Usage Examples:
  - `bin/stripe list-invoices --limit 20`
  - `bin/stripe list-invoices --status open --limit 50`

## `shopify`
- Registry Path: `/tools/shopify`
- Description: Shopify commerce operations tool with vault-backed access token and product listing commands.
- Binaries: `shopify`
- Usage Examples:
  - `bin/shopify list-products --limit 50`

## `doc-engine`
- Registry Path: `/tools/doc-engine`
- Description: Document engine for OCR via unstructured, conversion via pandoc, and Markdown print-to-Google-Doc.
- Binaries: `doc-engine`
- Usage Examples:
  - `bin/doc-engine ocr --file-path ./scanned-contract.pdf`
  - `bin/doc-engine convert --input-path ./draft.md --output-path ./draft.html --from-format markdown --to-format html`
  - `bin/doc-engine print-to-google-doc --title "Ops Brief" --markdown-file ./brief.md`

## `research`
- Registry Path: `/tools/research`
- Description: Multi-tier research gateway with cost-aware routing across web, neural, brief, and social tiers.
- Binaries: `research`
- Usage Examples:
  - `bin/research search --query "latest AI agent standards"`
  - `bin/research search --query "RAG retrieval benchmarks" --tier web --limit 10`
  - `bin/research search --query "Summarize this domain" --tier brief`
  - `bin/research search --query "Public sentiment on X" --tier social`

## `text-echo`
- Registry Path: `/tools/text-echo`
- Description: Deterministic echo utility for smoke-testing parser and wrapper pipelines.
- Binaries: `text-echo.py`
- Usage Examples:
  - `python3 bin/text-echo.py --json hello`

## `sync-scheduler`
- Registry Path: `/tools/sync-scheduler`
- Description: Calendar scheduling helper that uses `gws` to suggest Project Review time slots in deterministic JSON.
- Binaries: `sync-scheduler`
- Usage Examples:
  - `bin/sync-scheduler suggest --date 2026-02-25 --duration-minutes 45 --count 3 --json`
  - `bin/sync-scheduler suggest --date 2026-02-25 --start-hour 9 --end-hour 18 --json`

## `ad-intel`
- Registry Path: `/tools/ad-intel`
- Description: Ad performance monitor for Spend vs CTR anomaly detection using `ltr` bridge inputs and deterministic JSON alerts.
- Binaries: `ad-intel`
- Usage Examples:
  - `bin/ad-intel monitor --input ./campaign_metrics.json --json`
  - `bin/ad-intel monitor --spend-threshold-pct 35 --ctr-threshold-pct 20 --json`
  - `bin/ad-intel monitor --bridge-command "ltr news search 'meta ads benchmark ctr' --json" --json`

## `n8n-bridge`
- Registry Path: `/tools/n8n-bridge`
- Description: Secure webhook trigger bridge for local n8n workflows using n8n API wrapper commands with Vault-backed token retrieval.
- Binaries: `n8n-bridge`
- Usage Examples:
  - `bin/n8n-bridge trigger --workflow 123 --payload '{"job":"render"}' --json`
  - `bin/n8n-bridge trigger --workflow creative-pipeline --payload-file ./payload.json --json`

## `asset-filer`
- Registry Path: `/tools/asset-filer`
- Description: Uploads assets through `ltr` and registers metadata records for retrieval in `lsl_memory.assets`.
- Binaries: `asset-filer`
- Usage Examples:
  - `bin/asset-filer upload ./outputs/thumbnail.png --json`
  - `bin/asset-filer upload ./outputs/script.md --asset-type script --project-id launch-q2 --json`

## `social-ltr`
- Registry Path: `/tools/social-ltr`
- Description: Unified social wrapper for posting and comment retrieval across YouTube, TikTok, and X via `ltr`.
- Binaries: `social-ltr`
- Usage Examples:
  - `bin/social-ltr post --provider youtube --target-id <comment_id> --text "Thanks for your feedback" --json`
  - `bin/social-ltr fetch-comments --provider youtube --target-id <video_id> --json`
  - `bin/social-ltr post --provider x --target-id <thread_id> --text "Launch update" --json`
