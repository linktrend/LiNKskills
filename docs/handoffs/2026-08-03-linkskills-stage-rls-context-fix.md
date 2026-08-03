# Handoff — SKILLS-STAGE-RLS-CONTEXT-FIX (third correction)

**Date:** 2026-08-03  
**Branch:** `dev/cloudcursor/SKILLS-STAGE-RLS-CONTEXT-FIX`  
**Prior tip (HOLD):** `dd19d13d665711be2dccec71f2630499017a8e9b`  
**This tip:** see `git rev-parse HEAD` after push (commit below)

## Verdict

Independent Grok 4.5 High audit of the anonymous `append_event` bypass fix  
(working-tree audit before commit). Local ephemeral + gateway proofs green.  
Do **not** treat as stage/live self-approval — no Platform apply or redeploy.

## Root cause (third correction)

Tip `dd19d13` / code `1f8491b` closed arg/payload GUC overwrite on tenant writers,
but `PostgresGatewayStore.append_event` retained an anonymous write branch: when
neither bound identity nor payload carried actor/org, it set empty GUCs and
inserted `gateway_events` with null actor/org. Exact disposable proof:
`append_event({type: "anonymous-probe"})` with no bind succeeded.

## Fix (code only; no migration; no FORCE RLS)

- `postgres_store.py` `append_event`: remove anonymous branch; call
  `_require_bound_identity()` before any SQL; stamp row ownership from bound
  identity only; payload agreement-check unchanged.
- Missing/partial identity raises the same `postgres RLS requires bound…`
  ValueError already sanitized by service to `rls_org_required` (403).
- Request boundary: `service.dispatch` already wraps store ops in
  `identity(actor.actor_id, org)` from verified PACI; WRITE_OPERATIONS fail
  closed on null/empty orgId before handlers.

## Migration requirements

**None.** Do not reintroduce FORCE RLS (`000011`).

## Tests run

- `tests.gateway.test_postgres_bound_identity` — OK (11; includes anonymous /
  partial / payload-only / forge)
- Focused ephemeral: `test_append_event_anonymous_probe_rejected_no_null_row`,
  `test_append_event_partial_identity_and_forge_and_success_reuse` — OK
- `tests/gateway` discover (`test_*.py`) — 201 OK
- `tests/migrations` discover — 79 OK
- `pytest tests/gateway tests/migrations` — 280 passed

## Rollback

Revert Gateway deploy / branch tip to `dd19d13d665711be2dccec71f2630499017a8e9b`.
No migration rollback.

## Stage (Platform-only; not performed)

1. Redeploy Gateway from this tip.
2. Ensure `GRANT svc_lskills_runtime TO <gateway_login_role>;`
3. PACI write tokens must carry non-null `orgId`.
