# Handoff — SKILLS-STAGE-RLS-CONTEXT-FIX

**Date:** 2026-08-03  
**Branch:** `dev/cloudcursor/SKILLS-STAGE-RLS-CONTEXT-FIX`  
**Tip:** `da8141bc2a1da4b75dec45cc81f28ffda84da8b1` (code fix `c8c8f210f513ddad96c93c518656866cf96220e3`)  
**Start SHA:** `b7d46a1e1cc06f6662028f24e42eea73f2ed2368`

## Verdict

**PASS** (code + ephemeral proofs). Live stage apply remains **Platform-only** (not done here).

## Root cause

Both:

1. **Runtime:** nested `save_run` inside `run_atomic_idempotent` committed the outer Postgres transaction (`_atomic_depth == 1`), clearing transaction-local `SET LOCAL` actor/org GUCs before idempotency completion — and/or empty `orgId` failed `org_matches` as RLS `InsufficientPrivilege`.
2. **Server:** uncaught store exceptions dropped the HTTP connection instead of a structured envelope.

Policies already required `svc_lskills_runtime` + GUC match (`000006`/`000007`). Additive `000011` only FORCE-enables RLS (defense-in-depth).

## Stage apply (Platform)

1. Redeploy Gateway from tip `da8141b` (code `c8c8f21`).
2. Ensure DSN login role: `GRANT svc_lskills_runtime TO <gateway_login_role>;`
3. Apply `20260803_000011_lskills_gateway_force_rls.sql` (manifest + note under `docs/migrations/`).
4. PACI tokens for write clients must carry non-null `orgId` (null service org remains fail-closed `rls_org_required`).
5. Rollback: companion `*_down.sql` only (never drop schema).
