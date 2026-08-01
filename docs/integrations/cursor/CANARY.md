# Cursor Canary Plan (Stages 1–8)

- **Status:** Plan + fake/contract evidence only; Skills PACI machine-token **client + Cursor stdio MCP proxy implemented locally** (not live-proven)
- **Date:** 2026-08-01
- **Owner:** LiNKskills (Cursor product canary)
- **Live canary:** **false** — not started; project-scoped contract/docs only
- **Fragment:** `configs/fragments/cursor-skills-canary.mcp.json.example`
- **Entrypoint:** `python -m linkskills_mcp.paci_stdio_proxy` (PACI-aware; not bare `linkskills_mcp.server`)
- **PACI application steps:** `docs/integrations/cursor/PACI-CLIENT-APPLICATION-HANDOFF.md`
- **Rollback:** `docs/integrations/cursor/ROLLBACK.md`

## Platform pin (certified candidate ≠ live)

| Field | Value |
|---|---|
| Certified Platform candidate (read-only) | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` |
| Envelope | Frozen `platform.auth-token-envelope/0.1.0` (**not** `0.1.3-draft`) |
| Meaning | Candidate certification of Platform contract bytes ≠ live PACI issuer, hosting, credentials, or migration authority |

## Proven in this repo

**Fake/contract stage + Skills-owned PACI token client + stdio MCP proxy (local).** Project-scoped MCP/gateway unit tests, the example fragment (PACI placeholders + proxy module), `linkskills_client.paci_token_client`, and `linkskills_mcp.paci_stdio_proxy` exist. **No global Cursor mutation was performed** (no edits to `~/.cursor/mcp.json`, shared IDE Development `.cursor` symlink target, or user-level Cursor settings).

**Not live-proven:** Platform stage PACI issuer / JWKS / Skills credential registration are absent. Stages 3–8 remain blocked on Platform stage PACI. The certified Platform candidate pin above does **not** authorize starting a live canary.

## Auth path (Cursor consumer)

| Mode | When | Mechanism |
|---|---|---|
| **PACI proxy + HTTP Gateway (primary canary)** | `LINKSKILLS_CANARY=1` + `LINKSKILLS_AUTH_MODE=production` + `LINKSKILLS_MCP_UPSTREAM=http` + https `GATEWAY_URL` + `LINKSKILLS_PACI_*` | `paci_stdio_proxy` mints via `client_credentials` + `private_key_jwt` (ES256); injects `Authorization` to the durable stage Gateway over HTTPS; access TTL ≤900s; early renew &lt;20%; 401 invalidation + bounded retry |
| **PACI proxy in-process (opt-in only)** | Production only with `LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION=1` + `LINKSKILLS_ENV=stage\|production` + postgres store + DSN | Refused by default — never silently constructs an in-memory Gateway when ENV/store/DSN are missing |
| **Static bearer (local-test only)** | Explicit `LINKSKILLS_AUTH_MODE=local-test` (never canary) | `LINKSKILLS_LOCAL_TEST_STATIC_BEARER` / `GATEWAY_TOKEN` — **refused for `LINKSKILLS_CANARY`** |

HTTPS: `GATEWAY_URL` and PACI `token_endpoint` must be **https** outside `LINKSKILLS_AUTH_MODE=local-test` + loopback. Production canary fragment defaults to `LINKSKILLS_MCP_UPSTREAM=http`.

See Platform frozen `platform.auth-token-envelope/0.1.0` §§6–7 for assertion claims, 15-minute access tokens, no refresh token, and early renewal (&lt;20% TTL remaining). Do **not** cite `0.1.3-draft`.

## Stages

| Stage | Intent | Status in this repo |
|---|---|---|
| 1 | Prove fake/contract tests with isolated or project-scoped configuration | **Proven (fake/contract)** via gateway/MCP/client/PACI-proxy unit tests + example fragment |
| 2 | Inspect `.cursor` symlinks and shared/global settings read-only; record ownership | Documented in `docs/inventories/cursor-codex-mutation-surfaces.md` — no mutation |
| 3 | Stage read-only discovery | **Blocked** — requires Platform stage PACI issuer + Skills credential |
| 4 | Stage run/telemetry with non-side-effecting skills | **Blocked** — same |
| 5 | Exact packaged tool + artifact validation | **Blocked** on live stage; local dry-run only |
| 6 | Controlled failures / feedback / offline buffer | Client `LocalEventBuffer` unit-covered; not live Cursor |
| 7 | Librarian dry-run then evidence-backed write mode | Domain worker conformance only |
| 8 | Multi-day real use of representative canary set | Not started — blocked on Platform stage PACI |

## Guardrails

- Prefer project-scoped configuration from the example fragment.
- Launch **`linkskills_mcp.paci_stdio_proxy`** — never put bearer tokens in tool arguments, argv, logs, Git, or global Cursor config.
- Apply PACI env via the handoff doc; **do not edit global Cursor** (`~/.cursor/mcp.json`) without a coordinated maintenance window.
- Secrets never belong in the fragment; Platform issues Skills-only PACI credentials separately (never reuse Brain/OpenClaw clients).
- Private key: SecretRef **file path only** (`LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`) — never CLI args, never logs, never Git.
- Rollback path: `docs/integrations/cursor/ROLLBACK.md` (project-scoped disable + git revert; no live action).
