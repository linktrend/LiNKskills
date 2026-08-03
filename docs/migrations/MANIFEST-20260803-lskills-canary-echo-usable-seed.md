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
| 9 (**this package up**) | `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql` | `a1c6877589881d96a1ac32b4e5c0500a2e5311d4985f90966456c00bcf157977` |
| 10 (companion down) | `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed_down.sql` | `7c8e3e98f0d23dee34eeac54232be962cf7df383b5e9924861648e64485da49d` |

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
4. Fail-closed registry rows: `releases`, `execution_profiles`, `certifications` with sealed hashes.
   Existing conflict-key rows must match **all** pinned IDs/hashes/evidence; mismatch → `RAISE EXCEPTION`
   (transaction rolls back; no silent `ON CONFLICT DO NOTHING` promote).

Does **not** rewrite `000003`, drop schema, truncate, or disable triggers.

## Hash constants (sealed evidence)

Must match `evidence/phase10/sealed/canary-echo-sealed.json` on package finalize.
Evidence must be **release/promoting-mode** signed with an externally supplied issuer key
(never the repository-visible local HMAC key). Parent may refresh after re-seal.

| Constant | Value |
|---|---|
| `skill_release_hash` | `skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb` |
| `profile_hash` | `9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188` |
| `suite_hash` | `8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662` |
| `sealed_evidence_sha256` / `evidence_hash` | `bbaae7384cffd785b0585238174b103f213062428cf45160c9435fba660f80e0` |
| receipt `echo-hello` | `ec3227e77e1d19844c3d3a2d5de65520251263f228ab70a3f0bbe8a64cc8ed49` |
| receipt `echo-json` | `e02b150ab3915005b44d72c33687677849f27946e6191a57600960a006009005` |
| text-echo `source_hash` / `tool_hash` | `29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83` |
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
2. Confirm **only** this package's exact UUID/hash pins are removed. Later legitimate
   `canary-echo` / `0.2.0` rows with different IDs/hashes are left alone.
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
