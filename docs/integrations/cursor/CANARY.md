# Cursor Canary Plan (Stages 1–8)

- **Status:** Plan + fake/contract evidence only; Skills PACI machine-token **client implemented locally** (not live-proven)
- **Date:** 2026-07-30
- **Owner:** LiNKskills (Cursor product canary)
- **Fragment:** `configs/fragments/cursor-skills-canary.mcp.json.example`
- **PACI application steps:** `docs/integrations/cursor/PACI-CLIENT-APPLICATION-HANDOFF.md`

## Proven in this repo

**Fake/contract stage + Skills-owned PACI token client (local).** Project-scoped MCP/gateway unit tests, the example fragment (PACI placeholders), and `linkskills_client.paci_token_client` exist. **No global Cursor mutation was performed** (no edits to `~/.cursor/mcp.json`, shared IDE Development `.cursor` symlink target, or user-level Cursor settings).

**Not live-proven:** Platform stage PACI issuer / JWKS / Skills credential registration are absent. Stages 3–8 remain blocked on Platform stage PACI.

## Auth path (Cursor consumer)

| Mode | When | Mechanism |
|---|---|---|
| **PACI (primary canary)** | `LINKSKILLS_AUTH_MODE=production` + `LINKSKILLS_PACI_*` | `client_credentials` + `private_key_jwt` (ES256); private key via SecretRef file only |
| **Static bearer (local-test only)** | Explicit `LINKSKILLS_AUTH_MODE=local-test` | `LINKSKILLS_LOCAL_TEST_STATIC_BEARER` / `GATEWAY_TOKEN` — **retired as primary canary path** |

See Platform draft `platform.auth-token-envelope` §§6–7 for assertion claims, 15-minute access tokens, no refresh token, and early renewal (&lt;20% TTL remaining).

## Stages

| Stage | Intent | Status in this repo |
|---|---|---|
| 1 | Prove fake/contract tests with isolated or project-scoped configuration | **Proven (fake/contract)** via gateway/MCP/client tests + example fragment + PACI client unit tests |
| 2 | Inspect `.cursor` symlinks and shared/global settings read-only; record ownership | Documented in `docs/inventories/cursor-codex-mutation-surfaces.md` — no mutation |
| 3 | Stage read-only discovery | **Blocked** — requires Platform stage PACI issuer + Skills credential |
| 4 | Stage run/telemetry with non-side-effecting skills | **Blocked** — same |
| 5 | Exact packaged tool + artifact validation | **Blocked** on live stage; local dry-run only |
| 6 | Controlled failures / feedback / offline buffer | Client `LocalEventBuffer` unit-covered; not live Cursor |
| 7 | Librarian dry-run then evidence-backed write mode | Domain worker conformance only |
| 8 | Multi-day real use of representative canary set | Not started — blocked on Platform stage PACI |

## Guardrails

- Prefer project-scoped configuration from the example fragment.
- Apply PACI env via the handoff doc; **do not edit global Cursor** (`~/.cursor/mcp.json`) without a coordinated maintenance window.
- Secrets never belong in the fragment; Platform issues Skills-only PACI credentials separately (never reuse Brain/OpenClaw clients).
- Private key: SecretRef **file path only** (`LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`) — never CLI args, never logs, never Git.
