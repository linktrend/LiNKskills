# Handoff — SKILLS-STAGE-RLS-CONTEXT-FIX

**Date:** 2026-08-03  
**Branch:** `dev/cloudcursor/SKILLS-STAGE-RLS-CONTEXT-FIX`  
**Start SHA:** `b7d46a1e1cc06f6662028f24e42eea73f2ed2368`

## Verdict

**HOLD** for live stage (Platform apply + redeploy not done in this worktree).  
Local ephemeral / gateway proofs: green. Do not treat as stage self-approval.

## Root cause

`skills_run_start` → `PostgresGatewayStore.run_atomic_idempotent` INSERT into
`lskills.idempotency` raised `psycopg.errors.InsufficientPrivilege` because RLS
`WITH CHECK` requires transaction-local actor/org GUCs:

1. **Empty/missing orgId** → `set_config('app.current_org_id','',true)` →
   `nullif` → `org_matches` false → RLS deny on INSERT.
2. **Nested writer bug:** `_begin` treated `_atomic_depth > 1` only, so at
   depth `1` nested `save_run` called `rollback()` / `commit()` on the outer
   frame, clearing `SET LOCAL` GUCs mid-atomic transaction (SQLite already used
   deferred `_maybe_commit`).

Policies in `000006`/`000007` were already correct; no schema change required.

## Fix (code only; no live apply)

- `postgres_store.py`: `_require_rls_identity`; `set_config(..., true)` before
  writes; `_atomic_depth > 0` joins outer tx; `_maybe_commit` deferred nested
  commits; `get_idempotent` GUCs from bound identity only.
- `service.py`: fail-closed `rls_org_required` for write ops without orgId;
  sanitize `ValueError` / RLS privilege errors to `store_error`.
- `server.py`: catch unexpected exceptions → sanitized `internal_error` envelope
  (no connection drop / no policy text).

## Migration requirements

**None for this failure.** Additive FORCE RLS (`000011`) was authored then
removed — not required to fix INSERT RLS denial under a non-owner runtime role.

## Tests

- `tests/migrations/test_gateway_postgres_ephemeral.py` — same-tenant
  start/update/complete; cross-tenant denial; missing context; idempotency;
  rollback; GUC non-leakage on connection reuse.
- `tests/gateway/test_handler_error_sanitization.py` /
  `test_store_error_envelope.py` — sanitized HTTP envelopes.

## Rollback

Revert Gateway deploy to pre-fix SHA. No migration rollback needed.

## Stage (Platform-only; not performed here)

1. Redeploy Gateway from this tip.
2. Ensure `GRANT svc_lskills_runtime TO <gateway_login_role>;`
3. PACI write tokens must carry non-null `orgId`.
