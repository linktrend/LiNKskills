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
| 9 (**this package up**) | `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql` | `08013b5a3410a07459d1a33a3fed6121ee9ddad50f6632636863ef4700c76a66` |
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
Evidence must be **release/promoting-mode** signed with an externally supplied issuer key
(never the repository-visible local HMAC key). Parent may refresh after re-seal.

| Constant | Value |
|---|---|
| `skill_release_hash` | `skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb` |
| `profile_hash` | `4e146372eb9e0e07c09ce1cd20d6bda3199d7847637c2e93bbf35b2bdde0a4f9` |
| `suite_hash` | `8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662` |
| `sealed_evidence_sha256` / `evidence_hash` | `f5b7a8517130ee55e011ac93408f3c042f3e0efb77176344413ab7a3e8888f72` |
| receipt `echo-hello` | `fb8669da859b2a890b614993ab500f5d794f4027191b2d1dcd2a665925c35aca` |
| receipt `echo-json` | `f10a02b1e130092f0fe4e302b46f2e846553b278adaaa4696dee4f28e8f089fa` |
| text-echo `source_hash` / `tool_hash` | `6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0` |
| `issuer_id` | `linkskills-eval-runner-sealed-linux` |
| sealed image digest (release host) | `sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de` |

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
