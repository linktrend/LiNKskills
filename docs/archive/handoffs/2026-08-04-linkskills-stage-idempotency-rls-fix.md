# Handoff — SKILLS-STAGE-IDEMPOTENCY-RLS-FIX

**Date:** 2026-08-04
**Branch:** `dev/cloudcursor/SKILLS-STAGE-IDEMPOTENCY-RLS-FIX`
**Start SHA:** `eaf397042d575e74951c862b27f9489ac4d9f352`
**This tip:** `5efff786535193d5fe164bc4f7e1fbb592c37c8a` (code fix; docs pins may follow on branch HEAD)
**Packet:** SKILLS-STAGE-IDEMPOTENCY-RLS-FIX

## Verdict

**PASS** locally (ephemeral Postgres under restricted `svc_lskills_gateway`
LOGIN / NOBYPASSRLS + structural migration package). Do **not** treat as
stage/live self-approval — no Platform apply or redeploy from this lane.

## Root cause

PACI `skills_list` is file-catalog and never exercises Postgres RLS. The first
governed write on `skills_run_start` is `run_atomic_idempotent` →
`INSERT lskills.idempotency`. Policies are `TO svc_lskills_runtime` with
actor+org WITH CHECK via transaction-local GUCs. Stage DSN
`svc_lskills_gateway` was not expressed in Skills migrations (membership was
ops-only), so a login with table grants but no runtime membership hits
default-deny RLS (`InsufficientPrivilege: new row violates row-level security
policy`). Separately, empty/cleared GUCs produce the same error even with
membership. Prior GUC-binding code on `development` is preserved; this packet
adds the missing schema contract + stage-shaped proofs.

## Fix

1. **Additive `000011`** — create `svc_lskills_gateway` when absent (NOLOGIN /
   NOBYPASSRLS), `GRANT svc_lskills_runtime TO svc_lskills_gateway`, tighten
   `gateway_events` runtime policy to require actor+org (drop null/null
   anonymous branch). No FORCE RLS, SECURITY DEFINER, BYPASSRLS, or hardcoded
   stage IDs.
2. **Code** — reset leftover/aborted transaction before entering
   `run_atomic_idempotent` outer depth so SET LOCAL ROLE + GUCs always apply
   on a clean transaction.
3. **Tests** — native Postgres adversarial suite under restricted gateway
   LOGIN; production-shaped `SkillsGatewayService` start→update→complete (+
   safe tool dry-run) under the same role; structural package hash pins.

## Migration requirements (Platform-only apply)

- Up: `supabase/migrations/20260804_000011_lskills_gateway_role_rls_contract.sql`
- Down: `…_gateway_role_rls_contract_down.sql`
- Manifest: `docs/migrations/MANIFEST-20260804-lskills-gateway-role-rls-contract.md`
- Note: `docs/migrations/GATEWAY-ROLE-RLS-000011-NOTE.md`

If the stage DSN login is not named `svc_lskills_gateway`, Platform must still
`GRANT svc_lskills_runtime TO <gateway_login_role>`.

## Rollback

- Pre-apply: revert branch/commits.
- Post-apply: never edit applied `000011`; use companion down or a new additive
  forward-fix migration + coordinated Gateway code rollback.

## Stage (Platform-only; not performed)

1. Apply `000011` after `000010`.
2. Redeploy Gateway tip that binds PACI GUCs + SET LOCAL ROLE.
3. Confirm `GRANT svc_lskills_runtime TO <gateway_login_role>`.
4. Re-run PACI `skills_run_start` (list success alone is not proof).

## Out of bounds (honored)

Stage/cloud/live Lisa not touched. No credentials. No PR open/merge.
