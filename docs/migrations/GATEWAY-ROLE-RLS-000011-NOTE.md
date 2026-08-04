# Gateway role RLS contract 000011 — package note

**Packet:** `SKILLS-STAGE-IDEMPOTENCY-RLS-FIX`
**Authoring repo:** LiNKskills
**Live apply authority:** **LiNKplatform alone** applies live shared Supabase migrations.

## Why

Stage PACI `skills_list` can succeed (file-backed catalog) while `skills_run_start`
fails on `INSERT lskills.idempotency` with RLS `InsufficientPrivilege` when the
Gateway DSN role (`svc_lskills_gateway`) cannot assume `svc_lskills_runtime` and/or
transaction-local actor/org GUCs are missing. Policies remain `TO svc_lskills_runtime`
with actor+org WITH CHECK — this package wires the DSN role membership and closes
the anonymous `gateway_events` WITH CHECK hole.

## Ordered apply

1. Prerequisites: `000002` … `000010`.
2. This package: `20260804_000011_lskills_gateway_role_rls_contract.sql`
3. Rollback companion: `…_gateway_role_rls_contract_down.sql`

Manifest: `docs/migrations/MANIFEST-20260804-lskills-gateway-role-rls-contract.md`

## Runtime contract (unchanged)

```text
SET LOCAL ROLE svc_lskills_runtime;
select set_config('app.current_actor_id', '<paci-actor>', true);
select set_config('app.current_org_id', '<paci-org>', true);
```

Null/empty PACI `orgId` remains fail-closed for writes. Request-body actor/org
overrides are never trusted for GUCs.

## Explicit non-goals

- No FORCE RLS (prior handoff rejected FORCE as the anonymous-append fix).
- No SECURITY DEFINER / BYPASSRLS / service-role shortcut.
- No hardcoded stage actor/org UUIDs.
- No direct table grants to `svc_lskills_gateway` (writes via SET LOCAL ROLE).
