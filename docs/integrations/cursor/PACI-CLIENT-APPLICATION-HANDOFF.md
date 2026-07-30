# PACI Client Application Handoff — Project-Scoped Cursor (LiNKskills)

- **Date:** 2026-07-30
- **Owner:** LiNKskills
- **Scope:** Apply Skills PACI machine-token client config to **project-scoped** Cursor MCP only
- **Status:** Skills-owned path **implemented locally**; **not live-proven** (Platform PACI issuer absent)
- **Fragment:** `configs/fragments/cursor-skills-canary.mcp.json.example`
- **Client:** `packages/client/linkskills_client/paci_token_client.py`

## Maintenance-window note (global Cursor)

**Do not edit** `~/.cursor/mcp.json`, user-level Cursor settings, hooks, or the shared IDE Development `.cursor` symlink target for this canary.

If a global mutation ever becomes unavoidable: stop, obtain the coordinated Cursor maintenance window, document rollback, then apply once. Prefer project-scoped config exclusively for Stages 1–8 until Platform stage PACI is live.

## Prerequisites (Platform-owned — currently absent)

Before a live canary, Platform must provide independently verified:

1. Stage PACI authorization-server metadata + **token_endpoint** URI (Skills environment).
2. Skills-only `client_id` / credential / runtime binding (separate from Brain and OpenClaw).
3. Client JWKS registration for the ES256 public key (`kid` UUID).
4. Issuer JWKS for Gateway verification (resource server — not pasted into MCP env).
5. Least-privilege Skills scopes + Skills-only resource audience.
6. Secret injection path for the **private key PEM file** (GSM → SecretRef file on the canary host).

Until those exist, keep the fragment placeholders and run only local/fake PACI client tests.

## Exact application steps (project-scoped)

1. **Confirm branch / worktree** is LiNKskills; do not touch sibling repos.
2. **Copy** `configs/fragments/cursor-skills-canary.mcp.json.example` into the **project-scoped** Cursor MCP config surface for this repo only (Cursor project MCP / isolated canary config — **not** `~/.cursor/mcp.json`).
3. **Replace placeholders** (no real secrets in Git):

   | Env | Replace with |
   |---|---|
   | `LINKSKILLS_PACI_CLIENT_ID` | Skills stage `client_id` from Platform registration |
   | `LINKSKILLS_PACI_TOKEN_ENDPOINT` | Exact stage PACI token endpoint URI (Skills pin) |
   | `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE` | Absolute path to SecretRef-injected ES256 private key PEM |
   | `LINKSKILLS_PACI_CLIENT_KID` | Registered JWKS `kid` (UUID) |
   | `LINKSKILLS_PACI_SCOPE` | Least-privilege Skills scopes |
   | `LINKSKILLS_PACI_RESOURCE_AUDIENCE` | Skills-only audience (refuse Brain/OpenClaw values) |
   | `LINKSKILLS_PLATFORM_AUTHENTICATOR` | Platform-approved Gateway authenticator module |

4. **Private key custody**
   - File path only via `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`.
   - Never pass the key as a CLI arg, MCP `args` entry, chat paste, fixture, or log line.
   - Never commit the PEM; keep it outside the repo (approved secret store → host file).

5. **Keep** `LINKSKILLS_AUTH_MODE=production` and `LINKSKILLS_CANARY=1` for the canary profile.
6. **Do not** set `LINKSKILLS_CANARY_AUTHORIZATION` / `GATEWAY_TOKEN` / `LINKSKILLS_LOCAL_TEST_STATIC_BEARER` on the canary profile. Static bearers are **local-test only** (`LINKSKILLS_AUTH_MODE=local-test`) and are retired as the primary canary path.
7. **Start Gateway** with Platform-approved production authenticator + PACI verification path when live; MCP routes through the shared gateway service.
8. **Smoke (when Platform stage PACI exists):** project-scoped Cursor load → PACI mint → Gateway `skills_*` read-only discovery (Stage 3). Record evidence under `evidence/phase7/`.
9. **If mint fails:** fail closed. Do not fall back to static bearer in production/canary. Check endpoint pin, `client_id`, key file readability, and assertion clock — without printing key material.

## Local-test static bearer (explicit only)

For isolated unit/integration tests **without** a PACI issuer:

```text
LINKSKILLS_AUTH_MODE=local-test
LINKSKILLS_LOCAL_TEST_STATIC_BEARER=<test bearer>
```

Forbidden when `LINKSKILLS_CANARY=1` expects production cryptographic verification.

## Refusal rules

- Skills PACI `client_id` / audience / token_endpoint must **not** be reused for Brain or OpenClaw (`refuse_brain_openclaw_reuse`).
- No `refresh_token` handling; re-mint via `client_credentials` when remaining TTL &lt; 20%.
- Expected access token lifetime: 15 minutes (phase-1).

## Diagnostics

Safe status (no secrets): `PaciTokenClient.status()` / client construction errors that name env keys only.

## Residual gates

- Platform stage PACI issuer live + Skills credential issued
- Gateway PACI verifier proven against frozen Platform service
- Coordinated window only if global Cursor mutation is ever required (prefer never)
