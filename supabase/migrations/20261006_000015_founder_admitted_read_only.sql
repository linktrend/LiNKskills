-- Founder-approved, exact-release resource access without evaluation claims.
-- Existing qualified releases keep their qualification digest and behavior.
alter table lskills.provider_releases
  alter column qualification_sha256 drop not null;

alter table lskills.provider_releases
  drop constraint provider_releases_lifecycle_check;

alter table lskills.provider_releases
  add constraint provider_releases_lifecycle_check
  check (lifecycle in ('qualified','founder_admitted_read_only','revoked','quarantined'));

alter table lskills.provider_releases
  add constraint provider_release_admission_state_check
  check (
    (lifecycle = 'qualified' and qualification_sha256 is not null
      and manifest->>'qualification' = 'qualified')
    or
    (lifecycle = 'founder_admitted_read_only' and qualification_sha256 is null
      and manifest->>'qualification' = 'founder_admitted_read_only'
      and jsonb_typeof(manifest->'founder_admission') = 'object'
      and manifest->'founder_admission'->>'decision' = 'founder_approved'
      and manifest->'founder_admission'->>'evaluation' = 'not_performed')
    or lifecycle in ('revoked','quarantined')
  );
