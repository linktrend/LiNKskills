# Review queue migration 000008 — L5 merge note

Lane L3 authored additive migration:

- `supabase/migrations/20260730_000008_lskills_review_queue.sql`
- Manifest row in `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md`
- Librarian adapter: `packages/librarian_domain/linkskills_librarian/postgres_store.py`

## For L5 (handoffs / stage packets)

Please merge these refs into Librarian + stage readiness packets:

1. Ordered apply: `000007` (gateway persistence) then `000008` (review_queue).
2. Live apply authority remains **LiNKplatform only** — Skills agents do not apply to stage/prod.
3. Ephemeral proofs load the real `000008` SQL (not `tests/helpers/ephemeral_review_queue_ddl.sql`, which is now a non-DDL stub).
4. Runtime env for durable Librarian: `LINKSKILLS_LIBRARIAN_STORE=postgres` + rendered `LINKSKILLS_DATABASE_URL` (SecretRef). Production/stage forbids memory/sqlite.
5. Gateway production fail-closed: `LINKSKILLS_ENV` in `{stage,staging,production,prod}` implies `LINKSKILLS_GATEWAY_STORE=postgres` with DSN + schema probe.

## Schema summary

`lskills.review_queue` — org/actor columns, enum lifecycle
(`queued|claimed|in_progress|completed|failed|dead_letter|cancelled|expired`),
idempotency unique index, provenance jsonb, retry/dead-letter fields,
retention (`retain_until`), RLS for `svc_lskills_librarian` (org),
`svc_lskills_runtime` (actor+org insert/select), `svc_observer` (org read).
