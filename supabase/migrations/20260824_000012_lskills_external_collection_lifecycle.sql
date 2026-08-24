-- migrate:up
-- LiNKskills external collection lifecycle — PKT-03 / ISS-03
--
-- ADDITIVE ONLY.  LiNKplatform owns live application of this package.  An
-- imported vendor release is immutable; candidate arrival never changes a
-- current pointer.  Platform review/apply receipts are required for pointer
-- changes and rollback.

create schema if not exists lskills;

create table if not exists lskills.external_vendor_releases (
  vendor_release_id text primary key,
  collection_id text not null,
  vendor text not null,
  repository text not null,
  publisher text not null,
  license_ref text not null,
  source_ref text not null,
  source_path text not null,
  retrieved_at timestamptz not null,
  inventory_digest text not null,
  content_digest text not null,
  availability text not null default 'available',
  qualification text not null default 'unqualified',
  selectable boolean not null default false,
  files jsonb not null default '[]'::jsonb,
  immutable boolean not null default true,
  created_at timestamptz not null default now(),
  constraint external_vendor_release_hash_nonempty check (length(btrim(inventory_digest)) > 0),
  constraint external_vendor_release_license_nonempty check (length(btrim(license_ref)) > 0)
);

create table if not exists lskills.external_collection_manifests (
  collection_id text not null,
  version text not null,
  source_release text not null,
  license_ref text not null,
  release_ids jsonb not null default '[]'::jsonb,
  inventory_digest text not null,
  manifest_digest text not null,
  created_at timestamptz not null default now(),
  primary key (collection_id, version),
  constraint external_collection_manifest_hash_nonempty check (length(btrim(manifest_digest)) > 0)
);

create table if not exists lskills.external_adapted_releases (
  adapted_release_id text primary key,
  collection_id text not null,
  base_vendor_release_id text not null references lskills.external_vendor_releases(vendor_release_id),
  adaptation_ref text not null,
  adaptation_digest text not null,
  inventory_digest text not null,
  qualification text not null default 'unqualified',
  selectable boolean not null default false,
  files jsonb not null default '[]'::jsonb,
  immutable boolean not null default true,
  created_at timestamptz not null default now(),
  constraint external_adaptation_hash_nonempty check (length(btrim(adaptation_digest)) > 0)
);

create table if not exists lskills.external_update_candidates (
  candidate_id text primary key,
  idempotency_key text not null unique,
  collection_id text not null,
  current_release_id text,
  proposed_release_id text not null,
  candidate_digest text not null,
  signature text not null,
  signer text not null,
  status text not null default 'proposed',
  submitted_at timestamptz not null default now(),
  review_id text,
  platform_review_receipt_id text,
  platform_apply_receipt_id text,
  constraint external_candidate_digest_nonempty check (length(btrim(candidate_digest)) > 0),
  constraint external_candidate_signature_nonempty check (length(btrim(signature)) > 0)
);

create table if not exists lskills.external_librarian_reviews (
  review_id text primary key,
  candidate_id text not null references lskills.external_update_candidates(candidate_id),
  outcome text not null,
  reviewer text not null,
  evidence jsonb not null default '{}'::jsonb,
  reviewed_at timestamptz not null default now(),
  status text not null,
  constraint external_review_outcome_valid check (outcome in ('accept', 'adapt', 'postpone', 'reject'))
);

create table if not exists lskills.external_current_pointers (
  collection_id text primary key,
  current_release_id text,
  updated_at timestamptz not null default now(),
  platform_receipt_id text not null
);

create table if not exists lskills.external_platform_receipts (
  receipt_id text primary key,
  candidate_id text,
  operation text not null,
  authority text not null,
  candidate_digest text,
  release_id text,
  applied boolean not null default false,
  receipt jsonb not null default '{}'::jsonb,
  recorded_at timestamptz not null default now(),
  constraint external_receipt_authority check (authority = 'LiNKplatform')
);

create index if not exists external_vendor_collection_idx
  on lskills.external_vendor_releases (collection_id);
create index if not exists external_candidate_collection_idx
  on lskills.external_update_candidates (collection_id, status);
create index if not exists external_receipt_candidate_idx
  on lskills.external_platform_receipts (candidate_id);

-- RLS is explicit even though Platform supplies the production policies.
do $$
declare
  table_name text;
begin
  foreach table_name in array array[
    'external_vendor_releases', 'external_collection_manifests',
    'external_adapted_releases', 'external_update_candidates',
    'external_librarian_reviews', 'external_current_pointers',
    'external_platform_receipts'
  ] loop
    execute format('alter table lskills.%I enable row level security', table_name);
  end loop;
end $$;

-- The named service roles are granted only the bounded operations needed to
-- stage review data.  Live pointer writes remain Platform receipt operations.
grant select on lskills.external_vendor_releases,
  lskills.external_collection_manifests,
  lskills.external_adapted_releases,
  lskills.external_update_candidates,
  lskills.external_librarian_reviews,
  lskills.external_current_pointers,
  lskills.external_platform_receipts to svc_lskills_runtime;
-- Immutable release/manifests are insert-only for Librarian.  Candidate and
-- review rows remain mutable for bounded lifecycle status/receipt references.
grant select, insert on lskills.external_vendor_releases,
  lskills.external_collection_manifests,
  lskills.external_adapted_releases to svc_lskills_librarian;
grant select, insert, update on lskills.external_update_candidates,
  lskills.external_librarian_reviews to svc_lskills_librarian;

comment on table lskills.external_vendor_releases is
  'Immutable vendor bytes and per-file provenance/licence; unsafe originals remain preserved but nonselectable.';
comment on table lskills.external_update_candidates is
  'Signed idempotent proposals; candidate arrival never activates or switches a release.';
comment on table lskills.external_platform_receipts is
  'Platform-owned review/apply receipts required for current-pointer changes and rollback.';
