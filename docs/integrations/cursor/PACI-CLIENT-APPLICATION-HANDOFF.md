# PACI Client Application Handoff — Project-Scoped Cursor (LiNKskills)

- **Date:** 2026-08-01
- **Owner:** LiNKskills
- **Scope:** Apply Skills PACI machine-token client config to **project-scoped** Cursor MCP only
- **Status:** Skills-owned path **implemented locally**; **not live-proven** (Platform PACI issuer absent)
- **Live canary:** **false** — this handoff does not start a live canary
- **Fragment:** `configs/fragments/cursor-skills-canary.mcp.json.example`
- **Proxy:** `packages/mcp_server/linkskills_mcp/paci_stdio_proxy.py`
- **Client:** `packages/client/linkskills_client/paci_token_client.py`
- **Rollback:** `docs/integrations/cursor/ROLLBACK.md`

## Contract pins (frozen — not draft)

| Field | Value |
|---|---|
| Envelope | Frozen `platform.auth-token-envelope/0.1.0` (**supersedes** obsolete `0.1.3-draft`) |
| Access TTL | ≤900 seconds; no `refresh_token`; early renew when remaining TTL &lt; 20% |
| Assertion | `client_credentials` + `private_key_jwt` (ES256) per envelope §§6–7 |
| Certified Platform candidate (read-only) | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` |
| Candidate meaning | **Certified candidate ≠ live** PACI issuer, hosting, credentials, or migration authority |

## Maintenance-window note (global Cursor)

**Do not edit** `~/.cursor/mcp.json`, user-level Cursor settings, hooks, or the shared IDE Development `.cursor` symlink target for this canary.

If a global mutation ever becomes unavoidable: stop, obtain the coordinated Cursor maintenance window, document rollback (`docs/integrations/cursor/ROLLBACK.md`), then apply once. Prefer project-scoped config exclusively for Stages 1–8 until Platform stage PACI is live.

## Prerequisites (Platform-owned — currently absent)

Before a live canary, Platform must provide independently verified:

1. Stage PACI authorization-server metadata + **token_endpoint** URI (Skills environment, **https**).
2. Skills-only `client_id` / credential / runtime binding (separate from Brain and OpenClaw).
3. Client JWKS registration for the ES256 public key (`kid` UUID).
4. Issuer JWKS for Gateway verification (resource server — not pasted into MCP env).
5. Least-privilege Skills scopes + Skills-only resource audience.
6. Secret injection path for the **private key PEM file** (GSM → SecretRef file on the canary host).

Until those exist, keep the fragment placeholders and run only local/fake PACI client + proxy tests. Pinning the certified Platform candidate SHA does **not** satisfy these prerequisites.

## Exact application steps (project-scoped)

1. **Confirm branch / worktree** is LiNKskills; do not touch sibling repos.
2. **Copy** `configs/fragments/cursor-skills-canary.mcp.json.example` into the **project-scoped** Cursor MCP config surface for this repo only (Cursor project MCP / isolated canary config — **not** `~/.cursor/mcp.json`).
3. **Confirm entrypoint** is `python3 -m linkskills_mcp.paci_stdio_proxy` (not `linkskills_mcp.server`). The proxy mints PACI tokens and injects `Authorization` server-side.
4. **Replace placeholders** (no real secrets in Git):

   | Env | Replace with |
   |---|---|
   | `GATEWAY_URL` | Skills stage Gateway base URL (**https**) — required for production HTTP upstream |
   | `LINKSKILLS_PACI_CLIENT_ID` | Skills stage `client_id` from Platform registration |
   | `LINKSKILLS_PACI_TOKEN_ENDPOINT` | Exact stage PACI token endpoint URI (Skills pin, **https**) |
   | `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE` | Absolute path to SecretRef-injected ES256 private key PEM |
   | `LINKSKILLS_PACI_CLIENT_KID` | Registered JWKS `kid` (UUID) |
   | `LINKSKILLS_PACI_SCOPE` | Least-privilege Skills scopes |
   | `LINKSKILLS_PACI_RESOURCE_AUDIENCE` | Skills-only audience (refuse Brain/OpenClaw values) |
   | `LINKSKILLS_PLATFORM_AUTHENTICATOR` | Platform-approved Gateway authenticator module |
   | `LINKSKILLS_MCP_UPSTREAM` | **`http`** (production/canary default — durable stage Gateway). `in-process` is refuse-by-default under production; requires `LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION=1` + `LINKSKILLS_ENV=stage\|production` + postgres store + DSN |

5. **Private key custody**
   - File path only via `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`.
   - Never pass the key as a CLI arg, MCP `args` entry, chat paste, fixture, or log line.
   - Never commit the PEM; keep it outside the repo (approved secret store → host file).

6. **Keep** `LINKSKILLS_AUTH_MODE=production`, `LINKSKILLS_CANARY=1`, and `LINKSKILLS_MCP_UPSTREAM=http` for the canary profile (https `GATEWAY_URL` to durable stage Gateway).
7. **Do not** set `LINKSKILLS_CANARY_AUTHORIZATION` / `GATEWAY_TOKEN` / `LINKSKILLS_LOCAL_TEST_STATIC_BEARER` on the canary profile. Static bearers are **local-test only** (`LINKSKILLS_AUTH_MODE=local-test`) and are **refused** when `LINKSKILLS_CANARY=1`.
8. **HTTPS gate:** Outside local-test loopback, `GATEWAY_URL` and PACI endpoints must be https (coordinated with `LINKSKILLS_AUTH_MODE=local-test` + loopback for unit tests only).
9. **Refuse silent in-memory:** `LINKSKILLS_AUTH_MODE=production` never constructs an in-process in-memory Gateway because `LINKSKILLS_ENV`/store/DSN are missing — startup fails closed with an actionable error. In-process production is opt-in only (`LINKSKILLS_MCP_ALLOW_INPROCESS_PRODUCTION=1` + stage/prod env + postgres + DSN).
10. **Start Gateway** with Platform-approved production authenticator + PACI verification path when live; proxy injects short-lived bearer (TTL ≤900s, early renew &lt;20%, 401 invalidate + bounded retry) per frozen envelope `0.1.0`.
11. **Smoke (when Platform stage PACI exists):** project-scoped Cursor load → PACI mint → Gateway `skills_*` read-only discovery (Stage 3). Record evidence under `evidence/phase7/`.
12. **If mint fails:** fail closed. Do not fall back to static bearer in production/canary. Check endpoint pin, `client_id`, key file readability, and assertion clock — without printing key material.

## Local-test static bearer (explicit only)

For isolated unit/integration tests **without** a PACI issuer:

```text
LINKSKILLS_AUTH_MODE=local-test
LINKSKILLS_LOCAL_TEST_STATIC_BEARER=<test bearer>
GATEWAY_URL=http://127.0.0.1:<port>
```

Forbidden when `LINKSKILLS_CANARY=1` expects production cryptographic verification.

## Refusal rules

- Skills PACI `client_id` / audience / token_endpoint must **not** be reused for Brain or OpenClaw (`refuse_brain_openclaw_reuse`).
- No `refresh_token` handling; re-mint via `client_credentials` when remaining TTL &lt; 20%.
- Access token lifetime must not exceed **900 seconds**; longer `expires_in` is rejected (fail closed).
- Bearer never appears in tool arguments, MCP argv, logs, Git, or global Cursor config.
- Do not treat certified Platform candidate `421a35e…` as live stage PACI.

## Diagnostics

Safe status (no secrets): `PaciTokenClient.status()` / `PaciStdioMcpProxy.status()` / client construction errors that name env keys only. Optional JSON-RPC method `linkskills/paci_status`.

## Residual gates

- Platform stage PACI issuer live + Skills credential issued (beyond certified-candidate pin)
- Gateway PACI verifier proven against frozen Platform service (`platform.auth-token-envelope/0.1.0`)
- Coordinated window only if global Cursor mutation is ever required (prefer never)
