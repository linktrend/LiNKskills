-- migrate:down
-- Companion down for 20260803_000010_lskills_canary_echo_usable_seed.sql
--
-- Deletes ONLY this package's canary-echo rows. Never drop schema.
-- Live apply / rollback authority: LiNKplatform alone.
--
-- Delete order respects FKs:
--   certifications → execution_profiles (no cascade) + releases (cascade ok)
--   releases → catalog/eval_runs are independent

delete from lskills.certifications c
using lskills.releases r
where c.release_id = r.release_id
  and r.skill_id = 'canary-echo'
  and r.version = '0.2.0';

delete from lskills.certifications
where certification_id = 'c4e00010-a004-4000-8000-c4a47ee00001'::uuid;

delete from lskills.execution_profiles
where profile_key = 'canary-echo-0.2.0-linux-sealed-bwrap'
   or profile_id = 'c4e00010-a003-4000-8000-c4a47ee00001'::uuid;

delete from lskills.releases
where skill_id = 'canary-echo'
  and version = '0.2.0';

delete from lskills.eval_runs
where skill_id = 'canary-echo'
  and skill_version = '0.2.0';

delete from lskills.catalog
where skill_id = 'canary-echo'
  and version = '0.2.0';
