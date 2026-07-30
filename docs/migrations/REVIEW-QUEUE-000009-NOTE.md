# Review queue migration 000009 — actor isolation note

Lane B authored additive migration (does **not** rewrite 000008):

- `supabase/migrations/20260730_000009_lskills_review_queue_actor_isolation.sql`
- SHA-256: `acd0a1dbf81697d4e278ed4cdfa11d4b410b383420e02e6105940f578b6b6467`
- Manifest row in `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md`
- Librarian adapter gate: `packages/librarian_domain/linkskills_librarian/postgres_store.py`
  (`service_scope` / `LINKSKILLS_LIBRARIAN_SERVICE_SCOPE`)

## Policy contract

| Role | Default visibility | Privileged path |
|---|---|---|
| `svc_lskills_runtime` | actor + org | none |
| `svc_lskills_librarian` | actor + org | `app.librarian_service_scope=org` → any actor in bound org |
| `svc_observer` | org read (monitoring) | none (read-only) |

Same-org wrong-actor is **DENIED** for Librarian unless the privileged GUC is set for that transaction. Missing actor/org GUCs deny all rows.

## Runtime binding

- Default adapter: `service_scope="actor"` (fail-closed isolation).
- Approved Librarian service workers only: `service_scope="org"` or env `LINKSKILLS_LIBRARIAN_SERVICE_SCOPE=org`.
- Sets transaction-local `app.librarian_service_scope` via `set_config(..., true)` together with actor/org GUCs and `SET LOCAL ROLE svc_lskills_librarian`.

## For handoffs / Platform apply

1. Ordered apply: `000008` then `000009` (after `000007` gateway persistence).
2. Live apply authority remains **LiNKplatform only** — Skills agents do not apply to stage/prod.
3. Ephemeral proofs load real migration SQL files (never `tests/helpers/ephemeral_review_queue_ddl.sql`).
4. Prove: fresh through 000009; upgrade 000008→000009; wrong actor denial; wrong org denial; missing GUC denial; privileged org-scope cross-actor within org only.
