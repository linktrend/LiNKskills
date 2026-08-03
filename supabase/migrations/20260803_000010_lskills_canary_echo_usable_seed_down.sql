-- migrate:down
-- Companion down for 20260803_000010_lskills_canary_echo_usable_seed.sql
--
-- Deletes ONLY this package's exact fixed IDs/hashes. Never drop schema.
-- Later legitimate canary-echo 0.2.0 rows with different IDs/hashes are left alone.
-- Live apply / rollback authority: LiNKplatform alone.
--
-- Pinned constants (must match up migration; parent may refresh hashes later):
--   eval_run_id:       c4e00010-a001-4000-8000-c4a47ee00001
--   release_id:        c4e00010-a002-4000-8000-c4a47ee00001
--   profile_id:        c4e00010-a003-4000-8000-c4a47ee00001
--   certification_id:  c4e00010-a004-4000-8000-c4a47ee00001
--   release_hash:      skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb
--   profile_hash:      9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188
--   evidence_hash:     bbaae7384cffd785b0585238174b103f213062428cf45160c9435fba660f80e0
--
-- Delete order respects FKs:
--   certifications → execution_profiles (no cascade) + releases (cascade ok)
--   releases → catalog/eval_runs are independent

delete from lskills.certifications
where certification_id = 'c4e00010-a004-4000-8000-c4a47ee00001'::uuid
  and release_id = 'c4e00010-a002-4000-8000-c4a47ee00001'::uuid
  and profile_id = 'c4e00010-a003-4000-8000-c4a47ee00001'::uuid
  and evidence_hash = 'bbaae7384cffd785b0585238174b103f213062428cf45160c9435fba660f80e0';

delete from lskills.execution_profiles
where profile_id = 'c4e00010-a003-4000-8000-c4a47ee00001'::uuid
  and profile_key = 'canary-echo-0.2.0-linux-sealed-bwrap'
  and profile_hash = '9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188';

delete from lskills.releases
where release_id = 'c4e00010-a002-4000-8000-c4a47ee00001'::uuid
  and skill_id = 'canary-echo'
  and version = '0.2.0'
  and release_hash = 'skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb';

delete from lskills.eval_runs
where eval_run_id = 'c4e00010-a001-4000-8000-c4a47ee00001'::uuid
  and skill_id = 'canary-echo'
  and skill_version = '0.2.0'
  and efficiency_metrics->>'sealed_evidence_sha256'
      = 'bbaae7384cffd785b0585238174b103f213062428cf45160c9435fba660f80e0'
  and efficiency_metrics->>'skill_release_hash'
      = 'skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb'
  and efficiency_metrics->>'profile_hash'
      = '9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188';

delete from lskills.catalog
where skill_id = 'canary-echo'
  and version = '0.2.0'
  and frontmatter->>'skill_release_hash'
      = 'skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb'
  and frontmatter->>'profile_hash'
      = '9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188'
  and frontmatter->>'sealed_evidence_sha256'
      = 'bbaae7384cffd785b0585238174b103f213062428cf45160c9435fba660f80e0'
  and frontmatter->>'suite_hash'
      = '8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662';
