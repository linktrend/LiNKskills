# canary-echo usable seed 000010 — package note

**Packet add-on:** additive catalog usable-state seed for stage canary lifecycle.
**Authoring repo:** LiNKskills
**Live apply authority:** **LiNKplatform alone** applies live shared Supabase migrations.

## Ordered apply

1. Prerequisites: `000002` … `000009` (see `MANIFEST-20260727-lskills-registry-v0.1.md`).
2. This package: `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql`
3. Rollback companion: `…_canary_echo_usable_seed_down.sql` (deletes only canary-echo package rows).

Manifest: `docs/migrations/MANIFEST-20260803-lskills-canary-echo-usable-seed.md`

## Usable gate satisfaction

`enforce_usable_requires_passing_eval` requires a **passing** `lskills.eval_runs` row before `catalog.certification_state = usable`. This package:

1. Inserts catalog as `draft`
2. Inserts passing eval_run (sealed evidence refs in jsonb)
3. Updates catalog to `usable`

No trigger disable; no rewrite of `000003`.

## Stage readiness interaction

This package does **not** clear PREFLIGHT blockers B1–B5. Platform must still supply stage apply + backup receipts. Local structural tests only prove the SQL package is additive and hash-pinned.
