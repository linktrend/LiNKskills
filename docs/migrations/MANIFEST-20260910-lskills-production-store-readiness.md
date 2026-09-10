# Migration Manifest — lskills production store readiness v1.0.0

- **Date:** 2026-09-10
- **Package:** Hash-bound Platform-consumable `lskills` store (`000002`–`000013`)
- **Authoring repo:** LiNKskills
- **Live apply authority:** **LiNKplatform alone** under recovery task
  `01a0843c-0df9-74e2-907a-05c5f736d6ed`. Do not apply from a LiNKskills session.
- **Machine manifest:** `packages/persistence/MIGRATION-MANIFEST.json`
- **Compatible PostgreSQL major:** 17

This document is the human handoff for the same bytes pinned in the JSON
manifest. Digests in that file are authoritative; this file must not invent a
second pin.

## Prerequisites

1. Platform foundation on the **same** database: `platform.organizations`,
   `platform.member_role`, `platform.has_org_access(uuid, platform.member_role)`.
2. PostgreSQL **17**. Do not apply this package to another major.
3. Platform-owned PostgREST principals referenced by `000004` (`service_role`,
   `authenticator`) already exist if PostgREST exposure is in scope. Skills does
   not create LOGIN roles, passwords, or secret fixtures.
4. A filled Platform backup receipt covering schemas `platform` and `lskills`
   plus role/grant/RLS state **before** first live apply
   (`docs/migrations/BACKUP-RECEIPT-TEMPLATE.md`). Local ephemeral proof is not
   a backup receipt.

## Ordered files

Apply in manifest `order` (2 through 13). Recompute SHA-256 of on-disk SQL and
match `up_sha256` / `down_sha256`. Payload digest SHA-256 covers `000002`–
`000012` only (binder self-hash avoided). Package digest includes `000013`.

Companion down files exist for `000010`, `000011`, `000012`, and `000013` only.

## Least-privilege runtime grants and RLS

- Runtime role: `svc_lskills_runtime` (`NOLOGIN`, no `BYPASSRLS`).
- Gateway DSN contract (from `000011`): `GRANT svc_lskills_runtime TO
  svc_lskills_gateway` then `SET LOCAL ROLE` plus actor/org GUCs.
- Binder (`000013`): runtime and observer may `SELECT` `lskills.store_package`
  and `EXECUTE lskills.store_readiness_snapshot()`. No INSERT/UPDATE/DELETE
  grant or write policy on `store_package`.
- Snapshot function is `SECURITY INVOKER` and returns JSON without DSNs.
- Do not FORCE RLS in this binder, do not `GRANT` to `PUBLIC` / `anon`, and do
  not use `SECURITY DEFINER`.

## Forward verification (Platform)

```sql
select sha256 from /* independently hashed files */; -- must match JSON pins
select current_setting('server_version_num')::int / 10000 as postgres_major;
-- expect 17

set local role svc_lskills_runtime;
select lskills.store_readiness_snapshot();
-- expect ready=true, missing_relations=[], postgres_major=17, live_apply=false

insert into lskills.store_package(package_id, package_version, payload_digest_sha256)
values ('should-fail', '0', repeat('a', 64));
-- expect fail (RLS / privilege)
```

Idempotency: re-running `000013` succeeds when the payload digest matches and
raises on mismatch (fail closed). Re-running earlier files uses `IF NOT EXISTS`
/ policy drop-create as authored.

## Backup scope

Include `platform` + `lskills` schemas, `svc_lskills_*` / `svc_observer` role
memberships, RLS policies, and functions. Exclude GSM values, LOGIN passwords,
and any production row copies from Skills repositories.

## Rollback / forward-fix

- **Rollback:** Platform may apply the matching `*_down.sql` for additive
  packages `000010`–`000013` only after a governed backup. Earlier catalog/
  registry files have no companion down; use a new additive forward-fix rather
  than `drop schema lskills cascade`.
- **Forward-fix:** never rewrite applied SQL. Author a later dated migration
  and a new package version.

## Compatibility

Additive with existing `lskills` `000002`–`000012`. Does not copy Platform
implementation, mutate Server 01, or change consumer configuration. Live apply
remains HOLD until XP-01 / Platform receipts exist.

## Explicit non-claims

- This package is `source_only_no_apply`.
- Ephemeral PostgreSQL 17 proofs are not production apply evidence.
- `/ready` becoming 200 on Server 01 still requires Platform apply + runtime
  SecretRef rendering owned by the recovery task.
