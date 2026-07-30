# LiNKskills AuthClaims package-pin correction — 0.2.2

**Status:** `CORRECTION_COMPLETE` (Skills consumer pin only)  
**Scope:** Align live AuthClaims package pin to `@linktrend/platform-contracts@0.2.2`. **Not** merge of PR #22. **Not** Platform migrate/deploy/canary. **Not** Codex certification. **Not** other-repo edits.  
**Date / time:** 2026-07-30 Asia/Taipei  

## Session identity

| Field | Value |
|---|---|
| Role | LiNKskills implementer (package-pin correction) |
| Agent type | Cursor Local Agent |
| Model | Grok 4.5 High (`cursor-grok-4.5-high`) |
| Branch | `issue/21-linkskillsdevelopmentplan01` |
| PR | https://github.com/linktrend/LiNKskills/pull/22 (**draft; do not merge from this handoff**) |
| Base HEAD (exact clean start) | `2fb6f8d55f42c2350a6c528f32ff35023f544adc` |

## Authoritative live pin (after this correction)

| Field | Value |
|---|---|
| Contract | `platform.auth-claims/1.1.0` |
| Package | `@linktrend/platform-contracts@0.2.2` |
| Schema bytes SHA-256 | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` |
| contentHash | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` |
| Schema path | `packages/contracts/schemas/platform-auth-claims.v1.1.0.json` |
| Consumer pin | `docs/contracts/frozen/platform-auth-claims-v1.1.0.CONSUMER-PIN.md` |

## What changed

1. `PLATFORM_CONTRACTS_PACKAGE` in `packages/gateway/linkskills_gateway/auth.py`: `0.2.1` → `0.2.2` (contract version + schema hashes were already 1.1.0 / `c2e8bc68…` / `fb518834…`).
2. Aligned live consumer surfaces: 1.1.0 CONSUMER-PIN, OpenClaw MCP fragment auth block, OpenClaw HANDOFF, accept-valid-lskills fixture metadata, gateway test package assert, OPEN-ISSUES Wave 5 note.
3. Legacy `platform.auth-claims/1.0.0` / package `0.2.1` retained only as historical / rejection-only (`docs/contracts/frozen/platform-auth-claims-v1.0.0.CONSUMER-PIN.md` status → `historical_rejection_only`; historical wave handoffs untouched).
4. Added regression suite `tests/gateway/test_authclaims_pin_consistency.py` — fails if contract version, package version, or schema hashes disagree across auth constants, vendored schema, consumer pin, MCP fragment, and accept fixtures.

## Focused local proof

```text
PYTHONPATH=packages/gateway:packages/contracts:packages/catalog:. \
  python3 -m unittest \
  tests.gateway.test_authclaims_pin_consistency \
  tests.gateway.test_gateway.LocalUnsignedAuthTests -v
```

Result: **18 tests OK** (no CI poll; no merge).

## Ask of Platform (reconciliation)

1. Confirm `@linktrend/platform-contracts@0.2.2` is the published package identity for frozen `platform.auth-claims/1.1.0` with the schema SHA / contentHash above.
2. Treat Skills live pin as **0.2.2** going forward; do not ask Skills to re-advertise `0.2.1` for 1.1.0.
3. Do not migrate, deploy, or start canaries from this handoff.

## Non-claims

- No PR merge, CI/Bugbot poll, migration, deploy, or canary start.
- No edits to LiNKplatform, OpenClaw, or other repositories.
- No independent Codex verification claim.

## Exact clean HEAD

**Exact clean HEAD:** `706d05269228727c9cfdf134a60f3866801bf715`
