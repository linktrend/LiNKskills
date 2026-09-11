# Persistence forward-fix (production store package)

This package authors the Skills-owned durable store and the hash-bound
`lskills` migration package. **LiNKplatform alone applies live DDL** under
recovery task `01a0843c-0df9-74e2-907a-05c5f736d6ed`. Skills workers must not
print a live DSN, use production credentials, or apply live migrations.

`MemoryStore` remains source-level proof only and is never production-ready.

## Package identity

- Manifest: `packages/persistence/MIGRATION-MANIFEST.json`
- Binder: `supabase/migrations/20260910_000013_lskills_production_store_readiness.sql`
- Human handoff: `docs/migrations/MANIFEST-20260910-lskills-production-store-readiness.md`

Recompute SHA-256 of every listed SQL file before apply. Payload digest covers
`000002`–`000012`. Package digest includes the binder. Mismatch is fail-closed.

## Forward-fix

Never rewrite an applied migration. Author a later additive dated file, pin its
hashes in a new package version, and hand it to Platform with backup scope.

## Rollback

Use the companion `*_down.sql` files for `000010`, `000011`, `000012`, and
`000013` only as exact-object rollback. Earlier files have no down companion;
do not `drop schema lskills cascade`.
