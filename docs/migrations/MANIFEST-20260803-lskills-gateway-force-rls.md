# Migration Manifest — gateway FORCE RLS (000011)

- **Date:** 2026-08-03
- **Package:** Additive FORCE ROW LEVEL SECURITY on gateway persistence / run tables
- **Authoring repo:** LiNKskills
- **Live apply authority:** **LiNKplatform alone applies live** shared Supabase migrations. Do not apply from a LiNKskills agent session.

## Ordered files

Apply only after platform foundation + prior lskills migrations through `000007` (gateway persistence) are present. `000008`–`000010` may already be applied; this package does not depend on them.

| Order | File | SHA-256 |
|---|---|---|
| 1–8 (prerequisites) | See `MANIFEST-20260727-lskills-registry-v0.1.md` (`000002` … `000009`) | (pinned there) |
| 9 (optional prior) | `MANIFEST-20260803-lskills-canary-echo-usable-seed.md` (`000010`) | (pinned there) |
| 10 (**this package up**) | `supabase/migrations/20260803_000011_lskills_gateway_force_rls.sql` | `d3e8f9a9dcf71eb030451e41e97eb3715bdfe8c81ddc87804833342dc424646a` |
| 11 (companion down) | `supabase/migrations/20260803_000011_lskills_gateway_force_rls_down.sql` | `34ccd29081d090b3179d98efd90ce2966dc8a7fb9309d11428d348a795be12ac` |

Tests recompute SHA-256 of on-disk SQL bytes and require the manifest rows to match.

## Prerequisites

- Gateway persistence tables from `000007` (`idempotency`, `side_effect_intents`, `gateway_events`).
- Registry run tables from `000005` (`skill_runs`, `run_events`, `feedback`, `trace_to_eval_candidates`) with RLS enabled via `000005`/`000006`.
- Roles `svc_lskills_runtime` / `svc_lskills_librarian` / `svc_observer` exist.
- Platform grants `svc_lskills_runtime` to the Gateway stage login role so `SET LOCAL ROLE` succeeds.

## What this migration adds (additive only)

`FORCE ROW LEVEL SECURITY` on:

- `lskills.idempotency`
- `lskills.side_effect_intents`
- `lskills.gateway_events`
- `lskills.skill_runs`
- `lskills.run_events`
- `lskills.feedback`
- `lskills.trace_to_eval_candidates`

Does **not** change policies, grants, helpers, or disable RLS. Does **not** create login roles or grant `BYPASSRLS`.

## Apply / rollback instructions

### Apply (Platform only)

1. Confirm `000007` (and preferably `000006`) applied.
2. Confirm Gateway DSN login role is a member of `svc_lskills_runtime`.
3. Apply `20260803_000011_lskills_gateway_force_rls.sql` via Platform migration owner.
4. Run verification SQL below.
5. Redeploy Gateway build that binds PACI actor/org via `set_config(..., true)` per transaction before RLS writes.

### Rollback (Platform only)

1. Apply companion `20260803_000011_lskills_gateway_force_rls_down.sql`.
2. Confirm FORCE is off; ENABLE RLS + policies remain.
3. Do **not** `drop schema lskills cascade`.

## Verification SQL

```sql
select c.relname as table_name, c.relrowsecurity as rls, c.relforcerowsecurity as force_rls
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'lskills'
  and c.relkind = 'r'
  and c.relname in (
    'idempotency', 'side_effect_intents', 'gateway_events',
    'skill_runs', 'run_events', 'feedback', 'trace_to_eval_candidates'
  )
order by 1;
-- expect: rls=true and force_rls=true for all seven
```

## Explicit apply rule

**LiNKplatform alone applies live.** Skills agents must not apply to stage/prod / Supabase.
