# LiNKskills production execution — provisional handoff (2026-07-30)

**Status:** `PROVISIONAL` — LiNKskills-owned work complete for this packet; **not** merge/deploy/canary/Codex self-certification.  
**Executor:** Cursor Local Agent (Grok 4.5 High) + parallel Grok 4.5 High subagents  
**Date / time:** 2026-07-30 Asia/Taipei  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**PR:** https://github.com/linktrend/LiNKskills/pull/22 (**draft; do not merge**)  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**Execution prompt:** `docs/CURSOR-GROK-PRODUCTION-EXECUTION-PROMPT-2026-07-30.md`  
**Plan SHA-256 (verified):** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Exact heads

| Field | SHA |
|---|---|
| Exact start HEAD | `af1177a6428e3128b5360da5b92aecd670502589` |
| Session/prompt commit | `69c60b2f50143a09bb659ed3c2bd6234575cb64d` |
| Exact clean pushed HEAD | *(filled after final push — see agent response / git tip)* |

## Session

`docs/agent-sessions/active/20260730-cursor-grok-production-execution.md` (closed to `completed/` at end of packet).

## What landed (Skills-owned)

### 1. PACI resource-server consumer adapter (DRAFT envelope)

| Artifact | Path |
|---|---|
| Types / evidence markers | `packages/gateway/linkskills_gateway/paci_types.py` |
| JWKS (same-origin, no redirect, ≤5m cache) | `packages/gateway/linkskills_gateway/jwks.py` |
| ES256 JWT verify (`cryptography`) | `packages/gateway/linkskills_gateway/paci_jwt.py` |
| RFC 7662 introspection client | `packages/gateway/linkskills_gateway/introspection.py` |
| Authenticator + env factory | `packages/gateway/linkskills_gateway/paci_authenticator.py` |
| High-risk ops + operation-aware verify | `packages/gateway/linkskills_gateway/auth.py`, `server.py`, MCP `server.py` |
| Adversarial tests | `tests/gateway/test_paci_adversarial.py`, `paci_fakes.py` |
| Consumer adapter / delta packet | `docs/contracts/frozen/platform-auth-token-envelope-v0.1.CONSUMER-ADAPTER.md` |

**Mark everywhere:** `implemented but not proven against frozen Platform PACI service` (`platform.auth-token-envelope/0.1.3-draft`).

**AuthClaims live pin (unchanged):** `platform.auth-claims/1.1.0` · `@linktrend/platform-contracts@0.2.2` · schema `c2e8bc68…ddfa1` · contentHash `fb518834…ca567`.

### 2. Cursor PACI machine-token client

| Artifact | Path |
|---|---|
| Token client | `packages/client/linkskills_client/paci_token_client.py` |
| HTTP client PACI integration | `packages/client/linkskills_client/client.py` |
| Fragment + canary docs | `configs/fragments/cursor-skills-canary.mcp.json.example`, `docs/integrations/cursor/*` |
| Phase 7 honesty | `evidence/phase7/cursor-canary-status.json` |
| Tests | `tests/client/test_paci_token_client.py` |

Static bearer retired as primary canary path (local-test only). No global Cursor mutation.

### 3. Postgres persistence adapters

| Artifact | Path |
|---|---|
| Gateway Postgres store | `packages/gateway/linkskills_gateway/postgres_store.py` (+ `open_gateway_store` wire) |
| Librarian Postgres store | `packages/librarian_domain/linkskills_librarian/postgres_store.py` |
| Publisher Postgres registry | `packages/publisher/linkskills_publisher/postgres_registry.py` |
| Additive migration | `supabase/migrations/20260730_000007_lskills_gateway_persistence.sql` (SHA-256 `c26d1c55d9f87e242fe1e225fd4240cd911a5e0315d88500417d491689596222`) |
| Manifest update | `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md` |
| Ephemeral / unit tests | `tests/gateway/test_postgres_adapters_unit.py`, `tests/migrations/test_gateway_postgres_ephemeral.py` |

**Live apply:** Platform-owned only. Defaults remain SQLite/in-memory for local/test.

### 4. Deployable Gateway / MCP packaging + ops

| Artifact | Path |
|---|---|
| Installable pyprojects | root + `packages/{core,gateway,mcp_server,client,librarian_domain}/pyproject.toml` |
| Health / ready / metrics / drain | `packages/gateway/linkskills_gateway/ops.py`, `server.py` |
| Runbook rewrite | `docs/runbooks/PRODUCTION_OPERATIONS.md` |
| Platform service definition | `docs/deploy/GATEWAY-MCP-SERVICE-DEFINITION.md` |
| Env template | `deploy/vps/.env.example` |

Logic Engine remains retired. No Brain+Skills combined service.

### 5. Certification / classification honesty

| Artifact | Path |
|---|---|
| Classification ledger | `evidence/phase10/skill-classification-draft.json` (all 34 still draft; honest) |
| Rules | `evidence/phase10/CLASSIFICATION-HONESTY.md` |

macOS cannot certify (ADR 0009). No paid host created. No live promotion claimed.

### 6. Librarian + stage readiness packets

| Artifact | Path |
|---|---|
| Librarian stage packet | `docs/handoffs/2026-07-30-linkskills-librarian-stage-packet.md` |
| Stage readiness packet | `docs/handoffs/2026-07-30-linkskills-stage-readiness-packet.md` |
| Codex fragment handoff refresh | `docs/integrations/codex/HANDOFF.md` |

## Local proof (this packet)

| Command / suite | Result |
|---|---|
| `python3 validator.py --repo-root . --scan-all` | PASS (legacy ledger retention warnings only) |
| `python3 scripts/build-catalog-index.py --check` | PASS (34 skills) |
| `python3 scripts/check-service-ownership.py` | PASS |
| `python3 -m unittest discover -s tests/skill_runtime -v` | 6 OK |
| `.venv/bin/python -m pytest -q` (full PYTHONPATH) | **252 passed, 4 skipped, 189 subtests** |
| Focused PACI / ops / postgres / pin / client | OK prior to full suite |
| Secret scan (changed surfaces) | No private keys / live secrets introduced |
| CI / Bugbot | **Not polled** (deferred per prompt) |

## Evidence classes

| Class | Status |
|---|---|
| `local/fake` | PACI adapter, token client, Gateway ops, librarian worker, SQLite idempotency |
| Ephemeral Postgres | Adapter + RLS/idempotency proofs when Docker PG available |
| `live_stage` / `live_prod` | **Not claimed** — Platform env unreachable / PACI not deployed |

## Hard gates — stop here (external)

1. **Platform:** freeze PACI envelope; publish issuer/JWKS/introspection; separate Skills credentials; apply migrations live; stage hosting + secret injection + backup/rollback receipts.
2. **OpenClaw / Lisa Skills** prerequisite gate — not satisfied (Brain-first; Cursor/Codex readiness not recorded for Lisa).
3. **Independent LiNKskills Codex verification** of issue #21 / PR #22 — leave open.
4. **Paid execution host** — not created; needs Principal cost approval if required for Linux bwrap certification.
5. **Multi-day Cursor canary / production canary / general launch** — not started.

## Rollback

- Code: revert this branch tip relative to `af1177a…` / prior wave tips; do not apply `000007` live without Platform.
- If `000007` ever applied live: Platform-authored down migration only; never `drop schema lskills cascade`.
- Drain Gateway via `/drain` before cutover; cancel with `/drain/cancel`.

## Seven-classification ledger (approved Skills plan)

| Class | Meaning for this packet |
|---|---|
| Implemented + locally proven | AuthClaims 1.1 pin; PACI adapter (fake keys); Cursor PACI client (fake AS); Gateway ops surfaces; Postgres adapters (ephemeral); packaging; classification honesty; librarian local worker |
| Implemented, not Platform-proven | PACI resource-server path vs frozen live PACI service |
| Packaged, live-apply pending | Migrations through `000007` |
| Documented handoff only | Codex/OpenClaw fragments; librarian host integration; stage readiness packet |
| Blocked external | Live stage/prod PACI + hosting; OpenClaw Lisa Skills; Codex independent verification |
| Deliberately deferred | Org RLS on catalog.org_id; dollar-cost dashboard; `lib/skill_runtime` retirement |
| Forbidden / not done | Merge PR; deploy; migrate live; mutate global Cursor; edit sibling repos; invent live endpoints; paid hosts; self-certify Codex |

## Ask of next owners

1. **Platform:** freeze envelope; stand up stage PACI; apply Skills migrations; return receipts so Skills can continue stage canary stages 1–8 in a later packet.
2. **LiNKskills Codex:** independent verification against plan hash `31a6cc70…fe88` and this tip.
3. **OpenClaw:** Lisa Skills remains blocked until Cursor+Codex readiness + Brain stage exit per OpenClaw plan.
4. **Principal:** no merge/promote from this handoff; cost packet required before any paid cert host.

## Non-claims

No PR merge, no CI wait, no live migrate/deploy/canary, no sibling repo edits, no production dataset mutation, no secret printing, no Codex self-certification.
