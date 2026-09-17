# Migration Manifest — provider-v2 runtime (successor SQL)

- **Date:** 2026-09-16
- **Package:** `lskills-provider-v2-runtime` v1.0.0
- **Authoring repo:** LiNKskills
- **Live apply:** LiNKplatform / Server01 only
- **Machine manifest:** `packages/persistence/MIGRATION-MANIFEST-PROVIDER-V2.json`
- **SQL:** `supabase/migrations/20260915031801_lskills_provider_v2_runtime.sql`
- **SHA-256:** `1262ad8200130d7127407d659fc0d9ddfdc5aacba164aab9fd8ad64ccdd914e1`

Prerequisite: production-store package 000002–000013 already applied. This file does not rewrite earlier migrations.

Runtime may SELECT publication and bindings; it cannot enable bindings. Receipts are actor/org isolated. Rollback retains tables.
