# Migration Manifest — lskills registry foundation v0.1

- **Date:** 2026-07-27
- **Package:** Phase 2 registry tables (additive)
- **Authoring repo:** LiNKskills
- **Live apply authority:** **LiNKplatform alone applies live** shared Supabase migrations. Do not apply from a LiNKskills agent session.

## Ordered files

Apply only after platform foundation + prior lskills catalog migrations are present.

| Order | File | SHA-256 |
|---|---|---|
| 1 (prerequisite, already landed) | `supabase/migrations/20260715_000002_lskills_catalog_core.sql` | `4991dd628cc501a1013a4d7c3d8f859274e62ff847e768f106b0e3c2b89d8414` |
| 2 (prerequisite, already landed) | `supabase/migrations/20260715_000003_lskills_catalog_seed.sql` | `5e8f58a7159ad09f0c6389e12060c6a9cc76ff73dcfc2397ddea256d47a75e82` |
| 3 (prerequisite, already landed) | `supabase/migrations/20260718_000004_lskills_postgrest_exposure.sql` | `4220d70b626313f572a38720958fb78550b3b89c0efab5366a449d33c0b22ca0` |
| 4 (**this package**) | `supabase/migrations/20260727_000005_lskills_registry_foundation.sql` | `36081765032f21dfd2dcca223035555e1e54b71298874235def8e0362c55c4ed` |
| 5 (RLS upgrade) | `supabase/migrations/20260728_000006_lskills_rls_actor_org_scope.sql` | `12c2e45e94fd9216a5857ce53ce299a953dc2ee869f89bcdb392857133df763d` |
| 6 (gateway persistence) | `supabase/migrations/20260730_000007_lskills_gateway_persistence.sql` | `c26d1c55d9f87e242fe1e225fd4240cd911a5e0315d88500417d491689596222` |
| 7 (librarian review_queue) | `supabase/migrations/20260730_000008_lskills_review_queue.sql` | `0d5cf1f6abf62bddffc2e494bd8fb7faabe5aceb44266d446bb71f1209f43bab` |
| 8 (review_queue actor isolation) | `supabase/migrations/20260730_000009_lskills_review_queue_actor_isolation.sql` | `acd0a1dbf81697d4e278ed4cdfa11d4b410b383420e02e6105940f578b6b6467` |

Additive follow-on (separate package, not part of this eight-row pin):
`docs/migrations/MANIFEST-20260803-lskills-canary-echo-usable-seed.md` (`000010` canary-echo usable seed).

Also requires LiNKplatform `platform` foundation (`platform.organizations`, roles helpers) already applied on the shared database.

## Prerequisites

- `lskills` schema exists with `catalog`, `telemetry`, `eval_runs`.
- Roles `svc_lskills_runtime`, `svc_lskills_librarian`, `svc_observer` exist (created by catalog_core; re-created idempotently if missing).
- Enum `lskills.certification_state` already exists (referenced by `lskills.certifications`).
- Gateway helpers from 000006 (`lskills.org_matches` / `lskills.actor_matches`) and 000007 tables present before 000008.
- Review queue table from 000008 present before 000009 actor-isolation upgrade.

## What this migration adds (additive only)

Tables: `releases`, `bundles`, `fragments`, `tools`, `execution_profiles`, `certifications`, `skill_runs`, `run_events`, `feedback`, `trace_to_eval_candidates`.

Gateway persistence add-on (000007): `idempotency`, `side_effect_intents`, `gateway_events`, plus additive `events_json` / `feedback_json` columns on `skill_runs`.

Librarian review queue (000008): `lskills.review_queue` + enum `lskills.review_queue_status` with tenant/actor RLS, idempotency keys, provenance, retry/dead-letter, retention, and indexes.

Review queue actor isolation (000009): replaces librarian org-only RLS with actor+org default; privileged cross-actor-within-org requires transaction-local `app.librarian_service_scope=org` for `svc_lskills_librarian`.

Does **not** drop or alter existing `catalog` / `telemetry` / `eval_runs` tables.

## Rollback / forward-fix

- **Rollback:** create a separately dated `*_down.sql` that drops only the additive tables/types introduced here. Never `drop schema lskills cascade` from the up file.
- **Forward-fix:** if a partial apply leaves some tables present, re-running the up file is largely idempotent (`create table if not exists`, `drop policy if exists` / recreate). Validate with verification SQL below before declaring success.

## Verification SQL

```sql
select table_name
from information_schema.tables
where table_schema = 'lskills'
  and table_name in (
    'releases', 'bundles', 'fragments', 'tools', 'execution_profiles',
    'certifications', 'skill_runs', 'run_events', 'feedback',
    'trace_to_eval_candidates', 'idempotency', 'side_effect_intents',
    'gateway_events', 'review_queue'
  )
order by table_name;

select c.relname as table_name, c.relrowsecurity as rls_enabled
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'lskills'
  and c.relkind = 'r'
  and c.relname in (
    'releases', 'bundles', 'fragments', 'tools', 'execution_profiles',
    'certifications', 'skill_runs', 'run_events', 'feedback',
    'trace_to_eval_candidates', 'review_queue'
  )
order by 1;

-- Existing core tables must still exist:
select count(*) as core_tables
from information_schema.tables
where table_schema = 'lskills'
  and table_name in ('catalog', 'telemetry', 'eval_runs');
```

Expected: registry + gateway + `review_queue` with RLS enabled; `core_tables = 3`.

## Explicit apply rule

**LiNKplatform alone applies live.** LiNKskills hands this manifest + SQL to the platform migration owner. Skills agents must not apply to stage/prod.
