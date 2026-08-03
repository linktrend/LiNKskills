# Gateway FORCE RLS migration 000011 — note

Lane authored additive migration (does **not** rewrite 000007):

- `supabase/migrations/20260803_000011_lskills_gateway_force_rls.sql`
- SHA-256: `d3e8f9a9dcf71eb030451e41e97eb3715bdfe8c81ddc87804833342dc424646a`
- Companion down: `20260803_000011_lskills_gateway_force_rls_down.sql`
- Manifest: `docs/migrations/MANIFEST-20260803-lskills-gateway-force-rls.md`

## Why

Gateway write paths (`idempotency`, runs, feedback, side-effect intents) already
enable RLS with actor/org GUC policies. Without `FORCE`, a table-owner DSN can
bypass policies. Stage write failures after PACI worked were primarily missing /
cleared transaction-local GUCs in the runtime adapter; FORCE is defense-in-depth
so owner connections cannot silently bypass tenant checks.

## Runtime contract (unchanged)

```text
SET LOCAL ROLE svc_lskills_runtime;
select set_config('app.current_actor_id', '<paci-actor>', true);
select set_config('app.current_org_id', '<paci-org>', true);
```

Null/empty `orgId` remains fail-closed for writes (AuthClaims allows null only
for `actorKind=service`; RLS `org_matches` still requires a non-empty org GUC).

## Platform apply checklist

1. Ordered apply after `000007` (+ `000006` helpers).
2. `GRANT svc_lskills_runtime TO <gateway_login_role>;` (ops, not this SQL).
3. Live apply authority: **LiNKplatform only** — do not mutate Supabase from Skills.
4. Redeploy Gateway with RLS-context fix before / with apply.
