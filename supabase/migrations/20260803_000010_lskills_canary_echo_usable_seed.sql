-- migrate:up
-- LiNKskills canary-echo usable-state SEED (additive package 000010).
--
-- Authoring repo: LiNKskills. Live apply authority: LiNKplatform alone.
-- Skills agents must not apply this to stage/prod/shared Supabase.
--
-- Prerequisites (ordered): 000002 catalog_core, 000003 seed (34 draft skills;
--   canary-echo NOT in that seed), 000004–000009 registry/RLS/gateway/review_queue.
-- Does NOT rewrite 000003. Additive INSERT/UPDATE only.
--
-- Usable gate (000002 trg_catalog_usable_requires_passing_eval):
--   1) INSERT catalog row as draft
--   2) INSERT a passing lskills.eval_runs row for (canary-echo, 0.2.0)
--   3) UPDATE catalog.certification_state → usable
-- Order is mandatory; do not disable the trigger or invent columns.
--
-- HASH CONSTANTS — must match evidence/phase10/sealed/canary-echo-sealed.json
-- on package finalize. Parent may refresh these after a toolchain-hash re-seal.
--   skill_release_hash: skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac
--   profile_hash:       b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5
--   suite_hash:         8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662
--   sealed_evidence_sha256 (file bytes):
--                       eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2
--   receipt_hashes:     8168d400…, 348e69a2…
--   text-echo source/tool_hash:
--                       6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0
--
-- DOWN: separately dated companion
--   20260803_000010_lskills_canary_echo_usable_seed_down.sql
-- deletes ONLY this package's rows. Never drop schema.

-- ---------------------------------------------------------------------------
-- 1) Catalog row — draft first (trigger rejects usable without passing eval)
-- ---------------------------------------------------------------------------
insert into lskills.catalog (
  skill_id,
  version,
  org_id,
  display_name,
  description,
  format_profile,
  frontmatter,
  disclosure_refs,
  eval_suite_ref,
  certification_state,
  min_reasoning_tier
) values (
  'canary-echo',
  '0.2.0',
  null,
  'canary-echo',
  'Safe no-side-effect stage lifecycle canary that echoes tokens via packaged text-echo under sealed Eval Runner certification.',
  'simple',
  jsonb_build_object(
    'name', 'canary-echo',
    'version', '0.2.0',
    'format_profile', 'simple',
    'release_tag', 'v0.2.0',
    'sealed_evidence_path', 'evidence/phase10/sealed/canary-echo-sealed.json',
    'skill_release_hash', 'skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac',
    'profile_hash', 'b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5',
    'suite_hash', '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662',
    'sealed_evidence_sha256', 'eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2'
  ),
  jsonb_build_object(
    'advanced', 'skills/canary-echo/advanced/advanced.md',
    'schemas', 'skills/canary-echo/references/schemas.json'
  ),
  'skills/canary-echo/references/eval-suite.yaml',
  'draft',
  'fast'
)
on conflict (skill_id, version) do nothing;

-- ---------------------------------------------------------------------------
-- 2) Passing eval_run bound to sealed evidence identity (existing columns only)
--    Evidence refs live in efficiency_metrics / size_metrics jsonb — no new cols.
-- ---------------------------------------------------------------------------
insert into lskills.eval_runs (
  eval_run_id,
  skill_id,
  skill_version,
  eval_suite_ref,
  rubric_scores,
  overall_score,
  passed,
  pass_threshold,
  efficiency_metrics,
  size_metrics,
  judge_model,
  judge_model_version,
  judge_tier
) values (
  'c4e00010-a001-4000-8000-c4a47ee00001'::uuid,
  'canary-echo',
  '0.2.0',
  'skills/canary-echo/references/eval-suite.yaml',
  '{"correctness": 1.0}'::jsonb,
  1.0,
  true,
  0.8,
  jsonb_build_object(
    'sealed_evidence_path', 'evidence/phase10/sealed/canary-echo-sealed.json',
    'sealed_evidence_sha256', 'eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2',
    'skill_release_hash', 'skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac',
    'profile_hash', 'b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5',
    'suite_hash', '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662',
    'receipt_hashes', jsonb_build_array(
      '8168d400dfc6d1458fd7c078b5aea4ab1708621e19d18def5c2d48f7cb475a3c',
      '348e69a2110abc99d8f0a25c44a43603f824319fb73bc066d054933a52b12f8e'
    ),
    'network_isolation', 'denied',
    'certified', true,
    'tool_calls', 2
  ),
  jsonb_build_object(
    'suite_id', 'canary-echo-catalog-suite',
    'suite_version', '0.2.0',
    'cases_passed', jsonb_build_array('echo-hello', 'echo-json'),
    'weighted_score', 1.0,
    'issuer_id', 'linkskills-eval-runner-sealed-linux'
  ),
  'linkskills-eval-runner-sealed-linux',
  'linkskills-eval-executor/0.4.0',
  'high'
)
on conflict (eval_run_id) do nothing;

-- ---------------------------------------------------------------------------
-- 3) Promote to usable only after a passing eval_run exists for this version
-- ---------------------------------------------------------------------------
update lskills.catalog
set
  certification_state = 'usable',
  updated_at = now(),
  frontmatter = coalesce(frontmatter, '{}'::jsonb) || jsonb_build_object(
    'sealed_evidence_path', 'evidence/phase10/sealed/canary-echo-sealed.json',
    'skill_release_hash', 'skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac',
    'profile_hash', 'b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5',
    'suite_hash', '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662',
    'sealed_evidence_sha256', 'eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2'
  )
where skill_id = 'canary-echo'
  and version = '0.2.0'
  and certification_state is distinct from 'usable';

-- ---------------------------------------------------------------------------
-- 4) Registry bindings (000005+) — releases / execution_profiles / certifications
-- ---------------------------------------------------------------------------
insert into lskills.releases (
  release_id,
  skill_id,
  version,
  release_hash,
  channel,
  content_manifest,
  immutable,
  metadata
) values (
  'c4e00010-a002-4000-8000-c4a47ee00001'::uuid,
  'canary-echo',
  '0.2.0',
  'skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac',
  'canary',
  jsonb_build_object(
    'skill_id', 'canary-echo',
    'version', '0.2.0',
    'format_profile', 'simple',
    'eval_suite_ref', 'skills/canary-echo/references/eval-suite.yaml',
    'suite_hash', '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662'
  ),
  true,
  jsonb_build_object(
    'package', '20260803_000010_lskills_canary_echo_usable_seed',
    'sealed_evidence_path', 'evidence/phase10/sealed/canary-echo-sealed.json',
    'sealed_evidence_sha256', 'eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2'
  )
)
on conflict (skill_id, version) do nothing;

insert into lskills.execution_profiles (
  profile_id,
  profile_key,
  profile_hash,
  runtime,
  adapter_version,
  toolchain,
  metadata
) values (
  'c4e00010-a003-4000-8000-c4a47ee00001'::uuid,
  'canary-echo-0.2.0-linux-sealed-bwrap',
  'b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5',
  'linux',
  'linkskills-eval-executor/0.4.0',
  jsonb_build_object(
    'tools', jsonb_build_array(
      jsonb_build_object('tool_id', 'text-echo', 'version', '1.0.0', 'source_hash', '6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0', 'tool_hash', '6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0')
    ),
    'network_isolation', 'denied',
    'host_sealed_path', 'linux-bwrap-or-approved-container'
  ),
  jsonb_build_object(
    'package', '20260803_000010_lskills_canary_echo_usable_seed',
    'issuer_id', 'linkskills-eval-runner-sealed-linux',
    'skill_release_hash', 'skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac'
  )
)
on conflict (profile_key) do nothing;

insert into lskills.certifications (
  certification_id,
  release_id,
  profile_id,
  eval_run_ref,
  evidence_hash,
  state,
  certified_at,
  metadata
)
select
  'c4e00010-a004-4000-8000-c4a47ee00001'::uuid,
  r.release_id,
  p.profile_id,
  'skills/canary-echo/references/eval-suite.yaml',
  'eeda71e04b6e1e697b67e9ddacf4b357426e9ecbeeecc21381f68912bfa7deb2',
  'usable'::lskills.certification_state,
  timestamptz '2026-08-03 09:02:58+00',
  jsonb_build_object(
    'package', '20260803_000010_lskills_canary_echo_usable_seed',
    'sealed_evidence_path', 'evidence/phase10/sealed/canary-echo-sealed.json',
    'receipt_hashes', jsonb_build_array(
      '8168d400dfc6d1458fd7c078b5aea4ab1708621e19d18def5c2d48f7cb475a3c',
      '348e69a2110abc99d8f0a25c44a43603f824319fb73bc066d054933a52b12f8e'
    ),
    'suite_hash', '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662',
    'skill_release_hash', 'skill-release:52be31db2d55866b5cfa36196c8d29a2ce3bf8e8833a1c54e588aade4b8d59ac',
    'profile_hash', 'b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5',
    'seed_eval_run_id', 'c4e00010-a001-4000-8000-c4a47ee00001'
  )
from lskills.releases r
cross join lskills.execution_profiles p
where r.skill_id = 'canary-echo'
  and r.version = '0.2.0'
  and p.profile_key = 'canary-echo-0.2.0-linux-sealed-bwrap'
on conflict (release_id, profile_id) do nothing;
