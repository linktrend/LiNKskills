-- Additive v2 publication and receipt storage. Live application: Server01 only.
-- Prerequisite: existing lskills schema and svc_lskills_runtime/librarian roles.
-- Recovery: roll back the application; retain these tables and their backup.
create table lskills.provider_releases (
  release_id text primary key,
  manifest jsonb not null check (jsonb_typeof(manifest) = 'object'),
  manifest_sha256 text not null check (manifest_sha256 ~ '^sha256:[0-9a-f]{64}$'),
  qualification_sha256 text not null check (qualification_sha256 ~ '^sha256:[0-9a-f]{64}$'),
  lifecycle text not null default 'qualified' check (lifecycle in ('qualified','revoked','quarantined')),
  published_at timestamptz not null default now(),
  check (release_id = (manifest->>'skill_id') || '@' || (manifest->>'version'))
);
create table lskills.provider_bindings (
  org_id text not null check (org_id <> ''),
  actor_id text not null check (actor_id <> ''),
  runtime_binding_id text not null check (runtime_binding_id <> ''),
  runtime_profile text not null check (runtime_profile <> ''),
  release_ids text[] not null default '{}',
  enabled boolean not null default false,
  primary key (org_id, actor_id, runtime_binding_id)
);
create table lskills.provider_receipts (
  org_id text not null check (org_id <> ''),
  actor_id text not null check (actor_id <> ''),
  kind text not null check (kind in ('use','feedback')),
  receipt_id text not null check (length(receipt_id) between 1 and 256),
  request_hash text not null,
  record jsonb not null check (jsonb_typeof(record) = 'object'),
  created_at timestamptz not null default now(),
  primary key (org_id, actor_id, kind, receipt_id),
  check (octet_length(record::text) <= 65536)
);
alter table lskills.provider_releases enable row level security;
alter table lskills.provider_bindings enable row level security;
alter table lskills.provider_receipts enable row level security;
revoke all on lskills.provider_releases, lskills.provider_bindings, lskills.provider_receipts from public;
grant select on lskills.provider_releases, lskills.provider_bindings to svc_lskills_runtime;
grant select, insert on lskills.provider_receipts to svc_lskills_runtime;
grant select, insert on lskills.provider_releases to svc_lskills_librarian;
grant update (lifecycle) on lskills.provider_releases to svc_lskills_librarian;
-- Consumer bindings remain Platform-owned configuration; runtime cannot activate itself.
create policy provider_release_read on lskills.provider_releases for select
  to svc_lskills_runtime, svc_lskills_librarian using (true);
create policy provider_release_publish on lskills.provider_releases for insert
  to svc_lskills_librarian with check (true);
create policy provider_release_revoke on lskills.provider_releases for update
  to svc_lskills_librarian using (true) with check (true);
create policy provider_binding_read on lskills.provider_bindings for select to svc_lskills_runtime
  using (org_id = current_setting('app.current_org_id', true)
    and actor_id = current_setting('app.current_actor_id', true));
create policy provider_receipt_read on lskills.provider_receipts for select to svc_lskills_runtime
  using (org_id = current_setting('app.current_org_id', true)
    and actor_id = current_setting('app.current_actor_id', true));
create policy provider_receipt_insert on lskills.provider_receipts for insert to svc_lskills_runtime
  with check (org_id = current_setting('app.current_org_id', true)
    and actor_id = current_setting('app.current_actor_id', true)
    and record->>'org_id' = org_id and record->>'actor_id' = actor_id
    and record->>'request_hash' = request_hash);
