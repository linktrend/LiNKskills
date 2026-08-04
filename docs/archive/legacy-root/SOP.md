# LiNKskills Library Master SOP (v2.0.0)

This document is the definitive Source of Truth for operating the LiNKskills Library.

## 1. Executive Summary
LiNKskills Library is the Venture Studio's shared AI operating layer: a **Shared Brain and Hands**.

- Shared Brain:
  - Common reasoning standards, workflows, skills, and validation rules.
  - Shared historical learning from failures and improvements.
- Shared Hands:
  - A unified tool registry that executes actions consistently across domains.

### Shared Logic, Unique Identity
- Shared logic:
  - All agents use the same `/skills` and `/tools` architecture.
  - All agents follow the same safety, validation, and audit protocols.
- Unique identity:
  - Each agent uses isolated identity contexts via Vault-managed secrets.
  - Supabase memory uses `agent_id` partitioning to prevent cross-agent data mixing.

Business outcome: consistent execution quality at scale, without sacrificing per-agent identity boundaries.

## 2. The Fortress
The Fortress is the security baseline for the library.

### Vault (Secrets)
Plain-English summary:
- Vault is the encrypted safe for keys and credentials.
- Credentials are not stored in source code.
- Access is gated by `LSL_MASTER_KEY`.

What this protects:
- Stripe, Shopify, Supabase, n8n, Langfuse, and other sensitive credentials.

### Sandbox (Execution Safety)
Plain-English summary:
- Sandbox runs commands in temporary isolated containers.
- Memory is restricted.
- Network is disabled by default.

What this protects:
- Host machine stability, repository integrity, and operational safety when executing risky commands.

## 3. How-To: Secrets & Keys
### Prerequisite
1. Set your master key in shell:
   - `export LSL_MASTER_KEY="<your-master-key>"`

### Add credentials to Vault
1. Stripe key:
   - `tools/vault/bin/vault set STRIPE_API_KEY "sk_live_..."`
2. Shopify token:
   - `tools/vault/bin/vault set SHOPIFY_ACCESS_TOKEN "shpat_..."`
3. Supabase URL and secret:
   - `tools/vault/bin/vault set SUPABASE_URL "https://<project>.supabase.co"`
   - `tools/vault/bin/vault set SUPABASE_SECRET_KEY "sb_secret_..."`
4. Store from file (example Google OAuth credentials):
   - `tools/vault/bin/vault set ltr.credentials.json /absolute/path/credentials.json`

### List stored credentials
1. List key names only:
   - `tools/vault/bin/vault list`

### Retrieve one credential
1. Read key value:
   - `tools/vault/bin/vault get STRIPE_API_KEY`

### Rotate credentials
1. Overwrite existing key with new value:
   - `tools/vault/bin/vault set STRIPE_API_KEY "sk_live_new..."`
2. Confirm key exists:
   - `tools/vault/bin/vault list`
3. Re-run dependent operation to verify.

## 4. How-To: Identities
### Goal
Move from one agent identity (Lisa) to another (Bob) without data leakage.

### Step-by-step
1. Register Bob-specific secrets in Vault (if applicable):
   - `tools/vault/bin/vault set BOB_SUPABASE_SECRET_KEY "sb_secret_..."`
2. Use `agent_id="bob"` in memory workflows:
   - `tools/memory/bin/memory remember --agent-id bob --project-id ops --content "..."`
   - `tools/memory/bin/memory add-note --agent-id bob --title "Daily" --md-content "# Bob Notes"`
3. Retrieve only Bob-scoped data:
   - `tools/memory/bin/memory recall --agent-id bob --project-id ops --query "..."`
   - `tools/memory/bin/memory get-note --agent-id bob --title "Daily"`

### Isolation guidance
- Minimum isolation: enforce `agent_id` usage in all memory/note operations.
- Strong isolation (optional): per-agent Supabase schema/table strategy managed by DB admin.

## 5. How-To: Execution
### Trigger CLI tools
1. Call the tool wrapper in `/tools/<tool>/bin/`.
2. Prefer JSON-compatible outputs for automation.
3. Examples:
   - `tools/gws/bin/gws drive files list --params '{"pageSize": 5}'`
   - `tools/ltr/bin/ltr news trending --limit 10`
   - `tools/n8n/bin/n8n trigger --workflow-id 123 --payload-json '{"lead_id":"abc"}'`
   - `tools/stripe/bin/stripe list-invoices --limit 20`
   - `tools/shopify/bin/shopify list-products --limit 50`

### Service Ownership Gate
1. Resolve service routing using `configs/service_ownership.json`.
2. Workspace services must route through `gws`.
3. Non-Workspace Google/non-Google/interim gap services must route through `ltr`.
4. Validate matrix integrity with `python3 scripts/check-service-ownership.py`.

### Apply Cognitive Skills (Mental Models)
Use the following model based on task shape:

| Situation | Skill to Apply | Why |
| :--- | :--- | :--- |
| Complex multi-domain objective | `task-decomposition` | Break into atomic, verifiable steps |
| High-trust factual output | `citation-enforcer` | Force evidence per claim |
| Final quality gate before delivery | `self-critique-loop` | Catch logic/factual errors pre-release |
| Improve system based on history | `self-improvement` | Use ledger trends to drive versioned upgrades |

## 6. The Catalog (Manifest-Driven)
Catalog validated against `manifest.json`.

### Tools (13)
| UID | Path | What It Does for the Business |
| :--- | :--- | :--- |
| `gws` | `tools/gws` | Primary Workspace CLI with pinned release/checksum verification. |
| `ltr` | `tools/ltr/src/cli.py` | Runtime gateway for non-Workspace Google services, non-Google services, and local runtime controls. |
| `playwright-cli` | `tools/playwright-cli` | Stateless web automation for screenshots, PDFs, codegen, and browser setup. |
| `fast-playwright` | `tools/fast-playwright` | Interactive browser session control for complex multi-step web tasks. |
| `vault` | `tools/vault` | Encrypts and manages credentials safely for all tools and agents. |
| `sandbox` | `tools/sandbox` | Runs commands in isolated containers to reduce host risk. |
| `usage` | `tools/usage` | Captures execution telemetry in Langfuse (with local fallback). |
| `memory` | `tools/memory` | Long-term operational memory + Markdown notes, scoped by agent identity. |
| `n8n` | `tools/n8n` | Creates, reads, activates, and triggers automated workflows. |
| `stripe` | `tools/stripe` | Provides invoice visibility for finance operations. |
| `shopify` | `tools/shopify` | Provides product visibility for commerce operations. |
| `doc-engine` | `tools/doc-engine` | OCR + format conversion + Markdown publishing to Google Docs. |
| `text-echo` | `tools/text-echo` | Deterministic smoke-test utility for wrapper and parser pipelines. |

### Skills (11)
| UID | Path | What It Does for the Business |
| :--- | :--- | :--- |
| `skill-template` | `skills/skill-template` | Baseline blueprint for production-grade skills. |
| `skill-architect` | `skills/skill-architect` | Creates, reverse-engineers, and refines skills at scale. |
| `tool-architect` | `skills/tool-architect` | Standardizes and packages tools for the global registry. |
| `workflow-architect` | `skills/workflow-architect` | Converts process requirements into deployed/tested n8n automations. |
| `repository-manager` | `skills/repository-manager` | Enforces session handoff discipline and repository safety rules. |
| `audit-protocol` | `skills/audit-protocol` | Requires predictive intent logging before write actions. |
| `git-safeguard` | `skills/git-safeguard` | Enforces pre-push review checklist to reduce release mistakes. |
| `task-decomposition` | `skills/task-decomposition` | Breaks complex initiatives into executable atomic plans. |
| `citation-enforcer` | `skills/citation-enforcer` | Increases trust by enforcing evidence-backed claims. |
| `self-critique-loop` | `skills/self-critique-loop` | Improves output quality with structured System 2 review. |
| `self-improvement` | `skills/self-improvement` | Uses execution history to propose versioned platform upgrades. |

## 7. Maintenance
### Validation (mandatory)
1. Run full compliance scan:
   - `python3 validator.py --repo-root . --scan-all`
2. Run targeted scan:
   - `python3 validator.py --repo-root . --path skills/<skill-name>`

### Library update procedure
1. Edit tool/skill artifacts.
2. Re-run validator.
3. Update `manifest.json` for version/catalog changes.
4. Use MAS scripts:
   - `./scripts/lsl-update.sh`
   - `python3 scripts/lsl-review.py --repo-root . --remote origin --output reports/sync-report.json`
   - `./scripts/lsl-deploy.sh`

### Security maintenance
- Keep `LSL_MASTER_KEY` outside committed files.
- Keep token/credential files out of git.
- Rotate sensitive keys on schedule and after suspected exposure.
- Prefer sandboxed execution for riskier commands.

### Git hygiene
- Required before push:
  - `git status`
  - `git diff --cached`
- Preferred branch prefixes:
  - `feat/`, `fix/`, `refactor/`
- Optional safety gate:
  - `bash skills/repository-manager/scripts/git-pre-commit.sh`

## 8. Troubleshooting

| Error / Signal | Root Cause | Verified Fix |
| :--- | :--- | :--- |
| `SECURE_ENV_REQUIRED` | `LSL_MASTER_KEY` is not set | `export LSL_MASTER_KEY="<value>"`, then rerun command |
| Google `403 Forbidden` | Token scopes stale/insufficient | For Workspace routes rerun `tools/gws/bin/gws auth login`; for non-Workspace routes rerun `tools/ltr/bin/ltr setup --config tools/ltr/src/credentials.json` |
| Vault key missing | Required key not stored in Vault | `tools/vault/bin/vault set <KEY> <VALUE_OR_FILE>` then retry |
| Vault decryption failure / locked behavior | Wrong `LSL_MASTER_KEY` for current `vault.bin` | Set correct master key and retry `tools/vault/bin/vault list` |
| `[UsageTracker] Disconnected: Running in local-only mode.` | Langfuse credentials unavailable/unreachable | Add `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` to Vault; optional `LANGFUSE_HOST` |
| Sandbox runtime failure | Docker missing, stopped, or image pull failure | Start/install Docker and rerun sandbox command |
| Validator structural failure | Missing required file/dir or schema/frontmatter mismatch | Read validator output, fix exact target, rerun full scan |
| n8n API auth failure | Missing/invalid `N8N_API_KEY` or `N8N_BASE_URL` | Reset keys in Vault and rerun n8n command |
| Stripe auth failure | Missing/invalid `STRIPE_API_KEY` | Rotate/add `STRIPE_API_KEY` in Vault and retry |
| Shopify auth failure | Missing/invalid `SHOPIFY_ACCESS_TOKEN` or store domain | Update `SHOPIFY_ACCESS_TOKEN` and `SHOPIFY_STORE_DOMAIN` in Vault |
