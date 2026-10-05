-- Additive provider storage repair. Platform applies this migration.
-- Resource bytes are bounded per row; provider_releases remains the immutable
-- release metadata/index. Existing embedded manifests remain readable.
create table if not exists lskills.provider_release_resources (
  release_id text not null references lskills.provider_releases(release_id) on delete cascade,
  resource_id text not null check (resource_id <> ''),
  content_digest text not null check (content_digest ~ '^sha256:[0-9a-f]{64}$'),
  media_type text not null default 'application/octet-stream',
  content bytea not null,
  primary key (release_id, resource_id)
);

alter table lskills.provider_release_resources enable row level security;
revoke all on lskills.provider_release_resources from public;
grant select on lskills.provider_release_resources to svc_lskills_runtime;
grant select, insert on lskills.provider_release_resources to svc_lskills_librarian;

create policy provider_resource_read on lskills.provider_release_resources
  for select to svc_lskills_runtime, svc_lskills_librarian using (true);
create policy provider_resource_publish on lskills.provider_release_resources
  for insert to svc_lskills_librarian with check (true);

comment on table lskills.provider_release_resources is
  'Immutable provider resource bytes stored separately from release metadata to keep publication and retrieval bounded.';
