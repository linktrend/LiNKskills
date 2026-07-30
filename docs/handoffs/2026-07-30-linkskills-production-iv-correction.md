# LiNKskills production independent-verification correction — handoff

**Status:** `CORRECTION_COMPLETE` — stop for LiNKskills Codex re-verification (do not self-certify)  
**Executor:** Cursor Local Agent (Grok 4.5 High) + parallel Grok 4.5 High subagents  
**Date / time:** 2026-07-30 Asia/Taipei  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**PR:** https://github.com/linktrend/LiNKskills/pull/22 (**draft; do not merge**)  
**Correction prompt:** `docs/CURSOR-GROK-PRODUCTION-INDEPENDENT-VERIFICATION-CORRECTION-2026-07-30.md`

## Exact heads

| Field | SHA |
|---|---|
| Exact start HEAD (IV correction) | `48fd7422f9fa14d39567190b54d15954b3384f8b` |
| Platform pin (frozen PACI authority) | `0455846487d0b8c583859060ba8b4be70e7f0b48` |
| Exact clean pushed HEAD |  |

## Platform pins / hashes adopted

| Item | Value |
|---|---|
| Envelope contract | `platform.auth-token-envelope/0.1.0` |
| Contracts package (PACI) | `@linktrend/platform-contracts@0.3.0` |
| Envelope schema bytes SHA-256 | `7173b9f9bca59ce8a0e3e3dc2b78b680dd07fdd2451215e3ecd97ff3dd463eed` |
| Envelope contentHash | `9335b1855c3b3a5ec01b40c18ea85a98826192cbfba3110e07399d896e890a12` |
| AuthClaims (unchanged) | `platform.auth-claims/1.1.0` · schema `c2e8bc68…ddfa1` · contentHash `fb518834…ca567` |
| Access-token max TTL | **900s** (3600s rejected) |
| Consumer pin | `docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.CONSUMER-PIN.md` |

## Corrections completed (1–10)

1. **Cursor PACI canary path** — `linkskills_mcp.paci_stdio_proxy` mints via `PaciTokenClient` / `SkillsGatewayClient.from_env`; Authorization injected server-side; static bearer refused for canary; fragment updated.
2. **Production persistence fail-closed** — stage/prod require `LINKSKILLS_GATEWAY_STORE=postgres` + DSN + probe; memory/sqlite local/test only.
3. **Librarian review_queue** — additive `20260730_000008_lskills_review_queue.sql` (SHA-256 `0d5cf1f6abf62bddffc2e494bd8fb7faabe5aceb44266d446bb71f1209f43bab`); adapter bound; ephemeral helper is not a live migration.
4. **Packaging / privacy** — explicit pyprojects (incl. publisher/eval_runner); hard-require privacy/core; isolated install proofs.
5. **Frozen PACI envelope** — repinned from draft `0.1.3-draft` to `0.1.0`; TTL≤900; Platform fixtures + signed adversarial suite.
6. **Introspection binding** — exact field match on `active:true`; SecretRef signer required outside local-test; stub local-test only.
7. **HTTPS** — non-test PACI/Gateway URLs require HTTPS; HTTP only local-test + loopback.
8. **Operator artifacts** — env names aligned; config contract test; migrations 000007+000008 in packets/manifest.
9. **Graceful drain/shutdown** — SIGTERM/SIGINT → drain → bounded wait → close store → honest exit.
10. **Evidence hygiene** — trailing whitespace cleaned for `git diff --check origin/development...HEAD`; atomic seven-class ledger.

## Migrations (Platform applies live)

| Order | File | SHA-256 |
|---|---|---|
| 6 | `20260730_000007_lskills_gateway_persistence.sql` | `c26d1c55d9f87e242fe1e225fd4240cd911a5e0315d88500417d491689596222` |
| 7 | `20260730_000008_lskills_review_queue.sql` | `0d5cf1f6abf62bddffc2e494bd8fb7faabe5aceb44266d446bb71f1209f43bab` |

## Local proof (record)

| Suite | Result |
|---|---|
| Focused PACI/MCP/client/postgres/packaging/shutdown/config | **103 passed** |
| Full pytest | **329 passed, 4 skipped, 189 subtests** (~140s) |
| Ephemeral Postgres (`test_gateway_postgres_ephemeral`) | **11 passed** |
| validator / catalog / ownership / skill_runtime | PASS / 34 skills / success / **6 OK** |
| `git diff --check origin/development...HEAD` | clean after whitespace normalization commit |
| Secret scan (changed surfaces) | no private keys / live secrets added |
| CI / Bugbot | **not polled** |

## Seven-classification ledger (atomic)

| Class | This packet |
|---|---|
| local implementation | Corrected PACI/MCP/proxy/persist/ops code + unit/fake proofs |
| installable packaging | pyprojects + isolated install proofs |
| frozen-contract conformance | Envelope `0.1.0` fixtures/hashes/TTL/HTTPS/introspection binding locally proven |
| stage | **Not claimed** |
| canary | **Not claimed / not started** |
| production | **Not claimed** |
| forbidden | No merge, CI poll, live migrate/deploy, sibling edits, self-certify |

## Residuals / hard gates for Codex + Platform

1. Platform live PACI issuer/JWKS/introspection still absent — local frozen conformance ≠ live stage.
2. Platform must apply `000007`/`000008` live.
3. OpenClaw Lisa Skills prerequisite unchanged.
4. Independent Codex re-verification required next.

## Non-claims

No PR merge/readiness change, no deploy/canary, no sibling-repo edits, no cost, no Codex self-certification.
