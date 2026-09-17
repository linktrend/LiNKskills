-- migrate:up
-- LiNKskills production store readiness binder — v1.0.0 (additive)
--
-- ADDITIVE ONLY. Does not rewrite 000002–000012 DDL, weaken RLS, grant BYPASSRLS,
-- create LOGIN roles, or install credentials. Records the Skills-owned package
-- identity so a runtime role can SELECT a sanitised readiness snapshot.
--
-- Live apply authority: LiNKplatform alone. Recovery task
-- 01a0843c-0df9-74e2-907a-05c5f736d6ed retains sole live migration, credential,
-- backup and runtime authority. Do not apply from a LiNKskills agent session.
--
-- Prerequisite: Platform foundation (platform.organizations, platform.member_role,
-- platform.has_org_access) plus lskills 000002–000012 on PostgreSQL 17.
-- Compatible major: 17. Payload identity (000002–000012) is documented in
-- packages/persistence/MIGRATION-MANIFEST.json; this binder does not embed the
-- overall package digest (avoids a self-hash cycle).

create extension if not exists "pgcrypto";

create schema if not exists lskills;

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'svc_lskills_runtime') then
    create role svc_lskills_runtime nologin nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'svc_observer') then
    create role svc_observer nologin nobypassrls;
  end if;
end $$;

create table if not exists lskills.store_package (
  package_id text primary key,
  package_version text not null,
  payload_digest_sha256 text not null
    constraint store_package_payload_digest_sha256_format
      check (payload_digest_sha256 ~ '^[0-9a-f]{64}$'),
  postgres_major_min integer not null default 17
    constraint store_package_postgres_major_min_check
      check (postgres_major_min = 17),
  apply_authority text not null default 'LiNKplatform'
    constraint store_package_apply_authority_check
      check (apply_authority = 'LiNKplatform'),
  status text not null default 'source_only_no_apply',
  recorded_at timestamptz not null default now()
);

comment on table lskills.store_package is
  'Skills-authored production store package identity. Platform applies; runtime may SELECT only.';

alter table lskills.store_package enable row level security;

drop policy if exists lskills_store_package_runtime_select on lskills.store_package;
create policy lskills_store_package_runtime_select on lskills.store_package
  for select to svc_lskills_runtime
  using (true);

drop policy if exists lskills_store_package_observer_select on lskills.store_package;
create policy lskills_store_package_observer_select on lskills.store_package
  for select to svc_observer
  using (true);

revoke all on table lskills.store_package from public;
grant select on lskills.store_package to svc_lskills_runtime, svc_observer;

-- Idempotent identity row. Mismatch of payload digest fail-closes (no silent replace).
insert into lskills.store_package (
  package_id,
  package_version,
  payload_digest_sha256,
  postgres_major_min,
  apply_authority,
  status
) values (
  'lskills-production-store-readiness',
  '1.0.0',
  '626b8b5874ab17a3a2bc77b323573daaa077e510009bb9d6d97c20026efb9774',
  17,
  'LiNKplatform',
  'source_only_no_apply'
)
on conflict (package_id) do update
set
  package_version = excluded.package_version,
  recorded_at = lskills.store_package.recorded_at
where lskills.store_package.payload_digest_sha256 = excluded.payload_digest_sha256
  and lskills.store_package.package_version = excluded.package_version
  and lskills.store_package.apply_authority = excluded.apply_authority;

do $$
declare
  expected text := '626b8b5874ab17a3a2bc77b323573daaa077e510009bb9d6d97c20026efb9774';
  actual text;
begin
  select payload_digest_sha256 into actual
  from lskills.store_package
  where package_id = 'lskills-production-store-readiness';
  if actual is distinct from expected then
    raise exception 'lskills store package payload digest mismatch';
  end if;
end $$;

create or replace function lskills.store_readiness_snapshot()
returns jsonb
language plpgsql
stable
security invoker
set search_path = lskills, pg_temp
as $$
declare
  missing text[] := '{}'::text[];
  required constant text[] := array[
    'catalog',
    'telemetry',
    'eval_runs',
    'releases',
    'bundles',
    'fragments',
    'tools',
    'execution_profiles',
    'certifications',
    'skill_runs',
    'run_events',
    'feedback',
    'trace_to_eval_candidates',
    'idempotency',
    'side_effect_intents',
    'gateway_events',
    'review_queue',
    'external_vendor_releases',
    'external_collection_manifests',
    'external_adapted_releases',
    'external_update_candidates',
    'external_librarian_reviews',
    'external_current_pointers',
    'external_platform_receipts',
    'store_package'
  ];
  rel text;
  pkg jsonb;
  pg_major integer;
begin
  foreach rel in array required loop
    if to_regclass('lskills.' || rel) is null then
      missing := array_append(missing, rel);
    end if;
  end loop;

  select jsonb_build_object(
    'package_id', package_id,
    'package_version', package_version,
    'payload_digest_sha256', payload_digest_sha256,
    'postgres_major_min', postgres_major_min,
    'apply_authority', apply_authority
  )
  into pkg
  from lskills.store_package
  where package_id = 'lskills-production-store-readiness';

  pg_major := current_setting('server_version_num')::integer / 10000;

  return jsonb_build_object(
    'ready', (coalesce(cardinality(missing), 0) = 0 and pkg is not null and pg_major = 17),
    'missing_relations', to_jsonb(missing),
    'package', pkg,
    'postgres_major', pg_major,
    'live_apply', false
  );
end;
$$;

revoke all on function lskills.store_readiness_snapshot() from public;
grant execute on function lskills.store_readiness_snapshot() to svc_lskills_runtime, svc_observer;

comment on function lskills.store_readiness_snapshot() is
  'Invoker-safe readiness snapshot for /ready consumers. Never returns DSNs or secrets.';
