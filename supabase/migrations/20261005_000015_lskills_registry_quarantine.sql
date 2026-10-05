-- Additive quarantine visibility gate for canonical registry rows.
alter table lskills.releases
  add column if not exists registry_lifecycle text not null default 'published'
  check (registry_lifecycle in ('quarantined','published','retired'));

drop policy if exists lskills_releases_runtime_read on lskills.releases;
create policy lskills_releases_runtime_read on lskills.releases
  for select to svc_lskills_runtime
  using (lskills.require_org_context() and registry_lifecycle <> 'quarantined');

drop policy if exists lskills_bundles_runtime_read on lskills.bundles;
create policy lskills_bundles_runtime_read on lskills.bundles
  for select to svc_lskills_runtime
  using (lskills.require_org_context() and exists (
    select 1 from lskills.releases r
    where r.release_id = bundles.release_id
      and r.registry_lifecycle <> 'quarantined'
  ));
