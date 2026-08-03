# Handoff — SKILLS-STAGE-RLS-CONTEXT-FIX (second correction)

**Date:** 2026-08-03  
**Branch:** `dev/cloudcursor/SKILLS-STAGE-RLS-CONTEXT-FIX`  
**Prior tip (HOLD):** `1136b31a0de45d2e7abcfc70660ce9ceb620de57`  
**This tip:** see `git rev-parse HEAD` after push (commit below)

## Verdict

**PASS** from independent Grok 4.5 High audit of the bound-identity GUC overwrite fix  
(working-tree audit before commit). Local ephemeral + gateway proofs green.  
Do **not** treat as stage/live self-approval — no Platform apply or redeploy.

## Root cause (second correction)

Tip `1136b31` fixed read-path GUC sourcing (`get_idempotent`, `get_side_effect_intent`)
but write paths still derived `app.current_actor_id` / `app.current_org_id` from
method `actor_id` args or payload via `_current_identity(actor_id=…)` /
`bind_identity(payload…)`. Under `identity(actor-a, org-a)`,
`reserve_idempotency(actor-b)` inserted actor-b/org-a; forged
`append_feedback` / `append_trace` / `append_event` payloads inserted foreign tenants.

## Fix (code only; no migration; no FORCE RLS)

- `postgres_store.py`: `_current_identity()` bound-only; `_require_bound_identity`;
  `_assert_write_actor_agrees` / `_assert_payload_identity_agrees`; all tenant
  writers stamp GUCs + row ownership from bound identity only.
- `service.py`: PACI bind once at `dispatch` via `identity(actor.actor_id, org)`;
  sanitize store identity mismatch → `identity_mismatch` (403).
- Tests: unit `test_postgres_bound_identity.py`; ephemeral adversarial proofs
  (forged actor/org, mixed, missing, same-tenant, nested forge, rollback/reuse).

## Migration requirements

**None.** Do not reintroduce FORCE RLS (`000011`).

## Tests run

- `tests.gateway.test_postgres_bound_identity` — OK
- `tests/gateway` discover (`test_*.py`) — 198 OK
- `tests/migrations` discover — 77 OK (includes ephemeral adversarial)

## Rollback

Revert Gateway deploy / branch tip to `1136b31a0de45d2e7abcfc70660ce9ceb620de57`.
No migration rollback.

## Stage (Platform-only; not performed)

1. Redeploy Gateway from this tip.
2. Ensure `GRANT svc_lskills_runtime TO <gateway_login_role>;`
3. PACI write tokens must carry non-null `orgId`.
