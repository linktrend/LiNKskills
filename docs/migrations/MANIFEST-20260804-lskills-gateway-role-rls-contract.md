# Migration Manifest — gateway role RLS contract (000011)

- **Date:** 2026-08-04
- **Package:** Additive `svc_lskills_gateway` → `svc_lskills_runtime` membership + fail-closed `gateway_events` WITH CHECK
- **Authoring repo:** LiNKskills
- **Live apply authority:** **LiNKplatform alone applies live** shared Supabase migrations. Do not apply from a LiNKskills agent session.

## Ordered files

Apply only after platform foundation + prior lskills migrations through `000010` are present.

| Order | File | SHA-256 |
|---|---|---|
| 1–10 (prerequisites) | See `MANIFEST-20260727-lskills-registry-v0.1.md` + `MANIFEST-20260803-lskills-canary-echo-usable-seed.md` (`000002` … `000010`) | (pinned there) |
| 11 (**this package up**) | `supabase/migrations/20260804_000011_lskills_gateway_role_rls_contract.sql` | `0a8c56ee8ac2b3368d2a0ea8f6cc98719ccbc852d884dc34bc0143d5c7984a73` |
| 12 (companion down) | `supabase/migrations/20260804_000011_lskills_gateway_role_rls_contract_down.sql` | `b538241ef3c95af5e1f51a4781c7600644365720343016d41f15a935e209af89` |

Tests recompute SHA-256 of on-disk SQL bytes and require the manifest rows to match.

## Prerequisites

- `lskills.idempotency` / `side_effect_intents` / `gateway_events` from `000007`.
- Actor/org helpers from `000006` (`lskills.actor_matches`, `lskills.org_matches`).
- Gateway code that `SET LOCAL ROLE svc_lskills_runtime` and binds PACI actor/org via transaction-local `set_config(..., true)`.

## What this migration adds (additive only)

1. Ensures `svc_lskills_gateway` exists as `NOLOGIN` / `NOBYPASSRLS` when absent (preserves a Platform-owned LOGIN of the same name).
2. `GRANT svc_lskills_runtime TO svc_lskills_gateway` so Gateway DSN sessions can `SET LOCAL ROLE`.
3. Replaces `lskills_gateway_events_runtime_all` so USING/WITH CHECK require actor+org GUC match (removes the historical null/null anonymous branch).

Does **not** FORCE RLS, SECURITY DEFINER, BYPASSRLS, disable RLS, PUBLIC grants, hardcoded stage IDs, or direct table grants to the gateway role.

## Apply / rollback instructions

### Apply (Platform only)

1. Confirm prerequisites through `000010` applied and verified.
2. Redeploy Gateway with GUC-bound `PostgresGatewayStore` (SET LOCAL ROLE + bound identity) before or with apply.
3. Apply `20260804_000011_lskills_gateway_role_rls_contract.sql` via Platform migration owner.
4. If the DSN login is **not** named `svc_lskills_gateway`, also run ops:
   `GRANT svc_lskills_runtime TO <gateway_login_role>;`
   (and optionally `GRANT svc_lskills_gateway TO <gateway_login_role>;`).
5. Run verification SQL below. Record Platform apply receipt.

### Rollback (Platform only)

1. Apply companion `20260804_000011_lskills_gateway_role_rls_contract_down.sql`.
2. Confirm runtime membership revoked from `svc_lskills_gateway` and `gateway_events` policy restored to the 000007 shape.
3. Do **not** `drop schema lskills cascade`. Do **not** drop a Platform LOGIN role.
4. Coordinated Gateway code rollback if leaving stage without membership/GUC binding.

## Verification SQL

```sql
select r.rolname, r.rolcanlogin, r.rolbypassrls,
       exists (
         select 1 from pg_auth_members m
         join pg_roles g on g.oid = m.roleid
         where m.member = r.oid and g.rolname = 'svc_lskills_runtime'
       ) as has_runtime_membership
from pg_roles r
where r.rolname = 'svc_lskills_gateway';
-- expect: rolbypassrls=false, has_runtime_membership=true

select polname, pg_get_expr(polqual, polrelid) as using_expr,
       pg_get_expr(polwithcheck, polrelid) as check_expr
from pg_policy
where polrelid = 'lskills.gateway_events'::regclass
  and polname = 'lskills_gateway_events_runtime_all';
-- expect: no null/null branch; actor_matches + org_matches only
```

## Forward-fix guidance (post-apply)

Never edit this applied migration. If a later defect needs schema change, author a new additive forward-fix migration and coordinate Gateway code rollback separately.
