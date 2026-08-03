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
-- FAIL-CLOSED: existing rows on conflict keys must match ALL pinned IDs/hashes/
-- evidence/profile/suite/tool constants below. Mismatch → RAISE EXCEPTION
-- (transaction rolls back; no partial usable promote).
--
-- BINDING RULE: sealed evidence must be release/promoting-mode signed with an
-- externally supplied issuer key (never the repository-visible local HMAC key).
-- Local non-promoting canaries must not refresh this package.
--
-- HASH CONSTANTS — must match evidence/phase10/sealed/canary-echo-sealed.json
-- on package finalize. Parent may refresh these after a toolchain-hash re-seal.
--   skill_release_hash: skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb
--   profile_hash:       9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188
--   suite_hash:         8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662
--   sealed_evidence_sha256 (file bytes):
--                       a0bb2d56703cb95a6766a8902176f613dffed6af39d798546b338c5b3d77c262
--   receipt_hashes:     4da15fe0…, 7a4b885d…
--   text-echo source/tool_hash:
--                       29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83
--
-- PACKAGE IDS (fixed):
--   eval_run_id:        c4e00010-a001-4000-8000-c4a47ee00001
--   release_id:         c4e00010-a002-4000-8000-c4a47ee00001
--   profile_id:         c4e00010-a003-4000-8000-c4a47ee00001
--   certification_id:   c4e00010-a004-4000-8000-c4a47ee00001
--
-- DOWN: separately dated companion
--   20260803_000010_lskills_canary_echo_usable_seed_down.sql
-- deletes ONLY this package's exact IDs/hashes. Never drop schema.

do $pkg$
declare
  -- Centralized pins (parent refreshes hash literals here after re-seal).
  c_skill_id            text := 'canary-echo';
  c_version             text := '0.2.0';
  c_eval_suite_ref      text := 'skills/canary-echo/references/eval-suite.yaml';
  c_sealed_path         text := 'evidence/phase10/sealed/canary-echo-sealed.json';
  c_skill_release_hash  text := 'skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb';
  c_profile_hash        text := '9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188';
  c_suite_hash          text := '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662';
  c_evidence_hash       text := 'a0bb2d56703cb95a6766a8902176f613dffed6af39d798546b338c5b3d77c262';
  c_receipt_hello       text := '4da15fe03cb8ac71d34e1b86169bfbb35f47c8c7aa411b93ab2519e075de56e8';
  c_receipt_json        text := '7a4b885d545d0e9352be5151869fe8b4c963332225de3a5eab4b8bfdc810fa99';
  c_tool_hash           text := '29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83';
  c_profile_key         text := 'canary-echo-0.2.0-linux-sealed-bwrap';
  c_issuer_id           text := 'linkskills-eval-runner-sealed-linux';
  c_adapter_version     text := 'linkskills-eval-executor/0.4.0';
  c_package_name        text := '20260803_000010_lskills_canary_echo_usable_seed';
  c_eval_run_id         uuid := 'c4e00010-a001-4000-8000-c4a47ee00001'::uuid;
  c_release_id          uuid := 'c4e00010-a002-4000-8000-c4a47ee00001'::uuid;
  c_profile_id          uuid := 'c4e00010-a003-4000-8000-c4a47ee00001'::uuid;
  c_certification_id    uuid := 'c4e00010-a004-4000-8000-c4a47ee00001'::uuid;
  c_certified_at        timestamptz := timestamptz '2026-08-03 09:50:05+00';
  c_description         text := 'Stage lifecycle canary that echoes tokens via packaged text-echo under sealed Eval Runner certification. No durable shared/repo/network side effects; workspace-scoped tool writes and mandatory ledger telemetry only.';
  v_frontmatter         jsonb;
  v_disclosure          jsonb;
  v_eff                 jsonb;
  v_size                jsonb;
  v_content_manifest    jsonb;
  v_release_meta        jsonb;
  v_toolchain           jsonb;
  v_profile_meta        jsonb;
  v_cert_meta           jsonb;
begin
  v_frontmatter := jsonb_build_object(
    'name', c_skill_id,
    'version', c_version,
    'format_profile', 'simple',
    'release_tag', 'v0.2.0',
    'sealed_evidence_path', c_sealed_path,
    'skill_release_hash', c_skill_release_hash,
    'profile_hash', c_profile_hash,
    'suite_hash', c_suite_hash,
    'sealed_evidence_sha256', c_evidence_hash
  );
  v_disclosure := jsonb_build_object(
    'advanced', 'skills/canary-echo/advanced/advanced.md',
    'schemas', 'skills/canary-echo/references/schemas.json'
  );
  v_eff := jsonb_build_object(
    'sealed_evidence_path', c_sealed_path,
    'sealed_evidence_sha256', c_evidence_hash,
    'skill_release_hash', c_skill_release_hash,
    'profile_hash', c_profile_hash,
    'suite_hash', c_suite_hash,
    'receipt_hashes', jsonb_build_array(c_receipt_hello, c_receipt_json),
    'network_isolation', 'denied',
    'certified', true,
    'tool_calls', 2
  );
  v_size := jsonb_build_object(
    'suite_id', 'canary-echo-catalog-suite',
    'suite_version', c_version,
    'cases_passed', jsonb_build_array('echo-hello', 'echo-json'),
    'weighted_score', 1.0,
    'issuer_id', c_issuer_id
  );
  v_content_manifest := jsonb_build_object(
    'skill_id', c_skill_id,
    'version', c_version,
    'format_profile', 'simple',
    'eval_suite_ref', c_eval_suite_ref,
    'suite_hash', c_suite_hash
  );
  v_release_meta := jsonb_build_object(
    'package', c_package_name,
    'sealed_evidence_path', c_sealed_path,
    'sealed_evidence_sha256', c_evidence_hash
  );
  v_toolchain := jsonb_build_object(
    'tools', jsonb_build_array(
      jsonb_build_object(
        'tool_id', 'text-echo',
        'version', '1.0.0',
        'source_hash', c_tool_hash,
        'tool_hash', c_tool_hash
      )
    ),
    'network_isolation', 'denied',
    'host_sealed_path', 'linux-bwrap-or-approved-container'
  );
  v_profile_meta := jsonb_build_object(
    'package', c_package_name,
    'issuer_id', c_issuer_id,
    'skill_release_hash', c_skill_release_hash
  );
  v_cert_meta := jsonb_build_object(
    'package', c_package_name,
    'sealed_evidence_path', c_sealed_path,
    'receipt_hashes', jsonb_build_array(c_receipt_hello, c_receipt_json),
    'suite_hash', c_suite_hash,
    'skill_release_hash', c_skill_release_hash,
    'profile_hash', c_profile_hash,
    'seed_eval_run_id', c_eval_run_id
  );

  -- ---------------------------------------------------------------------------
  -- 1) Catalog — check-then-insert (PK skill_id, version)
  -- ---------------------------------------------------------------------------
  if exists (
    select 1 from lskills.catalog
    where skill_id = c_skill_id and version = c_version
  ) then
    if not exists (
      select 1 from lskills.catalog
      where skill_id = c_skill_id
        and version = c_version
        and display_name = c_skill_id
        and description is not distinct from c_description
        and format_profile = 'simple'::lskills.format_profile
        and org_id is null
        and eval_suite_ref = c_eval_suite_ref
        and min_reasoning_tier is not distinct from 'fast'
        and disclosure_refs = v_disclosure
        and frontmatter->>'name' = c_skill_id
        and frontmatter->>'version' = c_version
        and frontmatter->>'format_profile' = 'simple'
        and frontmatter->>'release_tag' = 'v0.2.0'
        and frontmatter->>'sealed_evidence_path' = c_sealed_path
        and frontmatter->>'skill_release_hash' = c_skill_release_hash
        and frontmatter->>'profile_hash' = c_profile_hash
        and frontmatter->>'suite_hash' = c_suite_hash
        and frontmatter->>'sealed_evidence_sha256' = c_evidence_hash
    ) then
      raise exception
        'canary-echo 000010 fail-closed: catalog row for %/% exists but does not match pinned package constants',
        c_skill_id, c_version;
    end if;
  else
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
      c_skill_id,
      c_version,
      null,
      c_skill_id,
      c_description,
      'simple',
      v_frontmatter,
      v_disclosure,
      c_eval_suite_ref,
      'draft',
      'fast'
    );
  end if;

  -- ---------------------------------------------------------------------------
  -- 2) Passing eval_run — check-then-insert (PK eval_run_id)
  -- ---------------------------------------------------------------------------
  if exists (
    select 1 from lskills.eval_runs where eval_run_id = c_eval_run_id
  ) then
    if not exists (
      select 1 from lskills.eval_runs
      where eval_run_id = c_eval_run_id
        and skill_id = c_skill_id
        and skill_version = c_version
        and eval_suite_ref = c_eval_suite_ref
        and passed is true
        and overall_score = 1.0
        and pass_threshold = 0.8
        and judge_model = c_issuer_id
        and judge_model_version = c_adapter_version
        and judge_tier = 'high'::lskills.judge_tier
        and rubric_scores = '{"correctness": 1.0}'::jsonb
        and efficiency_metrics = v_eff
        and size_metrics = v_size
    ) then
      raise exception
        'canary-echo 000010 fail-closed: eval_runs row % exists but does not match pinned package constants',
        c_eval_run_id;
    end if;
  else
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
      c_eval_run_id,
      c_skill_id,
      c_version,
      c_eval_suite_ref,
      '{"correctness": 1.0}'::jsonb,
      1.0,
      true,
      0.8,
      v_eff,
      v_size,
      c_issuer_id,
      c_adapter_version,
      'high'
    );
  end if;

  -- ---------------------------------------------------------------------------
  -- 3) Promote to usable only after passing eval_run exists for this version
  -- ---------------------------------------------------------------------------
  update lskills.catalog
  set
    certification_state = 'usable',
    updated_at = now(),
    frontmatter = coalesce(frontmatter, '{}'::jsonb) || jsonb_build_object(
      'sealed_evidence_path', c_sealed_path,
      'skill_release_hash', c_skill_release_hash,
      'profile_hash', c_profile_hash,
      'suite_hash', c_suite_hash,
      'sealed_evidence_sha256', c_evidence_hash
    )
  where skill_id = c_skill_id
    and version = c_version
    and certification_state is distinct from 'usable';

  -- ---------------------------------------------------------------------------
  -- 4) Releases — check-then-insert (unique skill_id, version)
  -- ---------------------------------------------------------------------------
  if exists (
    select 1 from lskills.releases
    where skill_id = c_skill_id and version = c_version
  ) then
    if not exists (
      select 1 from lskills.releases
      where skill_id = c_skill_id
        and version = c_version
        and release_id = c_release_id
        and release_hash = c_skill_release_hash
        and channel = 'canary'::lskills.release_channel
        and immutable is true
        and content_manifest = v_content_manifest
        and metadata = v_release_meta
    ) then
      raise exception
        'canary-echo 000010 fail-closed: releases row for %/% exists but does not match pinned package IDs/hashes',
        c_skill_id, c_version;
    end if;
  else
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
      c_release_id,
      c_skill_id,
      c_version,
      c_skill_release_hash,
      'canary',
      v_content_manifest,
      true,
      v_release_meta
    );
  end if;

  -- ---------------------------------------------------------------------------
  -- 5) Execution profile — check-then-insert (unique profile_key)
  -- ---------------------------------------------------------------------------
  if exists (
    select 1 from lskills.execution_profiles where profile_key = c_profile_key
  ) then
    if not exists (
      select 1 from lskills.execution_profiles
      where profile_key = c_profile_key
        and profile_id = c_profile_id
        and profile_hash = c_profile_hash
        and runtime = 'linux'
        and adapter_version is not distinct from c_adapter_version
        and toolchain = v_toolchain
        and metadata = v_profile_meta
    ) then
      raise exception
        'canary-echo 000010 fail-closed: execution_profiles row % exists but does not match pinned package IDs/hashes/toolchain',
        c_profile_key;
    end if;
  else
    insert into lskills.execution_profiles (
      profile_id,
      profile_key,
      profile_hash,
      runtime,
      adapter_version,
      toolchain,
      metadata
    ) values (
      c_profile_id,
      c_profile_key,
      c_profile_hash,
      'linux',
      c_adapter_version,
      v_toolchain,
      v_profile_meta
    );
  end if;

  -- ---------------------------------------------------------------------------
  -- 6) Certification — check-then-insert (unique release_id, profile_id)
  -- ---------------------------------------------------------------------------
  if exists (
    select 1 from lskills.certifications
    where release_id = c_release_id and profile_id = c_profile_id
  ) then
    if not exists (
      select 1 from lskills.certifications
      where release_id = c_release_id
        and profile_id = c_profile_id
        and certification_id = c_certification_id
        and eval_run_ref is not distinct from c_eval_suite_ref
        and evidence_hash = c_evidence_hash
        and state = 'usable'::lskills.certification_state
        and certified_at = c_certified_at
        and metadata = v_cert_meta
    ) then
      raise exception
        'canary-echo 000010 fail-closed: certifications row for release/profile pins exists but does not match pinned evidence/IDs';
    end if;
  else
    insert into lskills.certifications (
      certification_id,
      release_id,
      profile_id,
      eval_run_ref,
      evidence_hash,
      state,
      certified_at,
      metadata
    ) values (
      c_certification_id,
      c_release_id,
      c_profile_id,
      c_eval_suite_ref,
      c_evidence_hash,
      'usable'::lskills.certification_state,
      c_certified_at,
      v_cert_meta
    );
  end if;
end
$pkg$;
