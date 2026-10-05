-- Additive quarantine visibility gate for canonical registry rows.
alter table lskills.releases
  add column if not exists registry_lifecycle text not null default 'published'
  check (registry_lifecycle in ('quarantined','published','retired'));

do $$
declare
  actual_type text;
  actual_not_null boolean;
  actual_default text;
  check_count integer;
  lifecycle_check_count integer;
  lifecycle_attnum smallint;
begin
  select format_type(a.atttypid, a.atttypmod), a.attnotnull, pg_get_expr(d.adbin, d.adrelid)
    into actual_type, actual_not_null, actual_default
  from pg_attribute a
  join pg_class c on c.oid = a.attrelid
  join pg_namespace n on n.oid = c.relnamespace
  left join pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum
  where n.nspname='lskills' and c.relname='releases'
    and a.attname='registry_lifecycle' and not a.attisdropped;
  if actual_type is distinct from 'text' then
    raise exception 'registry_lifecycle existing column has incompatible type: %', actual_type;
  end if;
  if not actual_not_null or actual_default is distinct from '''published''::text' then
    raise exception 'registry_lifecycle existing column has incompatible nullability/default';
  end if;
  select attnum into lifecycle_attnum from pg_attribute
  where attrelid = 'lskills.releases'::regclass
    and attname = 'registry_lifecycle' and not attisdropped;
  select count(*), count(*) filter (where
    c.convalidated
    and c.conkey = array[lifecycle_attnum]::smallint[]
    and regexp_replace(pg_get_constraintdef(c.oid), '[[:space:]]', '', 'g') =
      'CHECK((registry_lifecycle=ANY(ARRAY[''quarantined''::text,''published''::text,''retired''::text])))'
  ) into lifecycle_check_count, check_count
  from pg_constraint c join pg_class r on r.oid=c.conrelid join pg_namespace n on n.oid=r.relnamespace
  where n.nspname='lskills' and r.relname='releases' and c.contype='c'
    and c.conkey @> array[lifecycle_attnum]::smallint[];
  if lifecycle_check_count <> 1 or check_count <> 1 then
    raise exception 'registry_lifecycle allowed-values check must be validated and match the exact state set';
  end if;
end $$;

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
