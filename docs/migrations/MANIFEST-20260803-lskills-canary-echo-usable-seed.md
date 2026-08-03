# Migration Manifest — canary-echo usable seed (000010)

- **Date:** 2026-08-03
- **Package:** Additive canary-echo catalog usable-state + sealed eval/cert evidence seed
- **Authoring repo:** LiNKskills
- **Live apply authority:** **LiNKplatform alone applies live** shared Supabase migrations. Do not apply from a LiNKskills agent session.

## Ordered files

Apply only after platform foundation + prior lskills migrations through `000009` are present.

| Order | File | SHA-256 |
|---|---|---|
| 1–8 (prerequisites) | See `MANIFEST-20260727-lskills-registry-v0.1.md` (`000002` … `000009`) | (pinned there) |
| 9 (**this package up**) | `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql` | `d14c6bef9cccbed9d2d4a6fd3a01569697aba02d071bc8d9affdeea3fac06246` |
| 10 (companion down) | `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed_down.sql` | `4849474ab18186f2b118d62f4209cb179d326ce02e32ec931570933289138f6b` |

Tests recompute SHA-256 of on-disk SQL bytes and require the manifest rows to match.

## Prerequisites

- `lskills.catalog`, `lskills.eval_runs` from `000002`.
- Prior draft catalog seed `000003` (34 skills; **canary-echo is absent** there — this package adds it).
- Registry tables from `000005` (`releases`, `execution_profiles`, `certifications`).
- Trigger `enforce_usable_requires_passing_eval` remains enabled (this seed never disables it).

## What this migration adds (additive only)

1. `lskills.catalog` row for `canary-echo` / `0.2.0` (`format_profile=simple`, `org_id=null`).
2. Passing `lskills.eval_runs` row bound to sealed evidence identity (jsonb evidence refs only).
3. Catalog promotion to `usable` **after** the passing eval_run exists.
4. Idempotent registry rows: `releases`, `execution_profiles`, `certifications` with sealed hashes.

Does **not** rewrite `000003`, drop schema, truncate, or disable triggers.

## Hash constants (sealed evidence)

Must match `evidence/phase10/sealed/canary-echo-sealed.json` on package finalize.
Parent may refresh after toolchain-hash re-seal.

| Constant | Value |
|---|---|
| `skill_release_hash` | `skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac` |
| `profile_hash` | `b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5` |
| `suite_hash` | `8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662` |
| `sealed_evidence_sha256` / `evidence_hash` | `eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2` |
| receipt `echo-hello` | `8168d400dfc6d1458fd7c078b5aea4ab1708621e19d18def5c2d48f7cb475a3c` |
| receipt `echo-json` | `348e69a2110abc99d8f0a25c44a43603f824319fb73bc066d054933a52b12f8e` |
| text-echo `source_hash` / `tool_hash` | `6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0` |

## Apply / rollback instructions

### Apply (Platform only)

1. Confirm prerequisites `000002`–`000009` applied and verified.
2. Apply `20260803_000010_lskills_canary_echo_usable_seed.sql` via Platform migration owner.
3. Run verification SQL below.
4. Record Platform apply receipt (Skills agents do not invent stage receipts).

### Rollback (Platform only)

1. Apply companion `20260803_000010_lskills_canary_echo_usable_seed_down.sql`.
2. Confirm canary-echo catalog/eval/release/profile/cert rows are gone.
3. Do **not** `drop schema lskills cascade`.

## Verification SQL

```sql
select skill_id, version, certification_state, eval_suite_ref, format_profile
from lskills.catalog
where skill_id = 'canary-echo' and version = '0.2.0';
-- expect: usable, skills/canary-echo/references/eval-suite.yaml, simple

select eval_run_id, passed, overall_score, judge_tier,
       efficiency_metrics->>'sealed_evidence_path' as sealed_path
from lskills.eval_runs
where skill_id = 'canary-echo' and skill_version = '0.2.0'
order by created_at desc
limit 1;
-- expect: passed=true, overall_score=1.0, sealed path present

select release_hash, channel
from lskills.releases
where skill_id = 'canary-echo' and version = '0.2.0';

select profile_key, profile_hash
from lskills.execution_profiles
where profile_key = 'canary-echo-0.2.0-linux-sealed-bwrap';

select c.state, c.evidence_hash
from lskills.certifications c
join lskills.releases r on r.release_id = c.release_id
where r.skill_id = 'canary-echo' and r.version = '0.2.0';
```

## Explicit apply rule

**LiNKplatform alone applies live.** LiNKskills packages this manifest + SQL for the platform migration owner. Skills agents must not apply to stage/prod.
