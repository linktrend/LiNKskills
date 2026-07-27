-- migrate:up
-- LiNKskills registry foundation (Phase 2 additive tables) — v0.1
--
-- ADDITIVE ONLY. Extends the existing `lskills` schema created by
-- 20260715_000002_lskills_catalog_core.sql. Does NOT drop or rewrite
-- catalog / telemetry / eval_runs.
--
-- Authority: docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md
--            Phase 2 registry surfaces + ADRs 0002–0007.
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.
-- This file is authored in LiNKskills for review/handoff; do not apply
-- from a Skills agent session.
--
-- Prerequisite: 20260715_000002_lskills_catalog_core.sql (and platform
-- foundation roles/helpers) already present on the target database.

create extension if not exists "pgcrypto";

create schema if not exists lskills;

do $$
begin
  if not exists (
    select 1 from pg_type
    where typname = 'release_channel' and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.release_channel as enum ('internal', 'canary', 'stable');
  end if;

  if not exists (
    select 1 from pg_type
    where typname = 'run_status' and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.run_status as enum (
      'started', 'in_progress', 'completed', 'failed', 'cancelled'
    );
  end if;

  if not exists (
    select 1 from pg_type
    where typname = 'feedback_kind' and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.feedback_kind as enum (
      'correction', 'rating', 'friction', 'missing_step', 'invocation', 'other'
    );
  end if;

  if not exists (
    select 1 from pg_type
    where typname = 'trace_candidate_status' and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.trace_candidate_status as enum (
      'queued', 'accepted', 'rejected', 'converted', 'duplicate'
    );
  end if;
end $$;

-- ---------------------------------------------------------------------------
-- releases — immutable published skill versions (hash-addressed)
-- ---------------------------------------------------------------------------
create table if not exists lskills.releases (
  release_id uuid primary key default gen_random_uuid(),
  skill_id text not null,
  version text not null,
  release_hash text not null,
  channel lskills.release_channel not null default 'internal',
  source_commit text,
  content_manifest jsonb not null default '{}'::jsonb,
  published_at timestamptz not null default now(),
  immutable boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  constraint releases_skill_version_uniq unique (skill_id, version),
  constraint releases_hash_nonempty check (length(btrim(release_hash)) > 0)
);

create index if not exists releases_skill_id_idx on lskills.releases (skill_id);
create index if not exists releases_hash_idx on lskills.releases (release_hash);

comment on table lskills.releases is
  'Immutable published skill release records. Ordinary consumers bind to these hashes.';

-- ---------------------------------------------------------------------------
-- bundles — compiled Skill Pack artifacts for a release
-- ---------------------------------------------------------------------------
create table if not exists lskills.bundles (
  bundle_id uuid primary key default gen_random_uuid(),
  release_id uuid not null references lskills.releases(release_id) on delete cascade,
  bundle_hash text not null,
  format_profile text not null default 'heavy',
  storage_uri text,
  byte_size bigint,
  created_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  constraint bundles_hash_nonempty check (length(btrim(bundle_hash)) > 0)
);

create index if not exists bundles_release_id_idx on lskills.bundles (release_id);

-- ---------------------------------------------------------------------------
-- fragments — progressive disclosure levels 0–6
-- ---------------------------------------------------------------------------
create table if not exists lskills.fragments (
  fragment_id uuid primary key default gen_random_uuid(),
  release_id uuid not null references lskills.releases(release_id) on delete cascade,
  fragment_key text not null,
  disclosure_level smallint not null,
  title text not null,
  content_media_type text not null default 'text/markdown',
  content_hash text not null,
  content text,
  parent_fragment_key text,
  created_at timestamptz not null default now(),
  constraint fragments_level_range check (disclosure_level between 0 and 6),
  constraint fragments_release_key_uniq unique (release_id, fragment_key),
  constraint fragments_hash_nonempty check (length(btrim(content_hash)) > 0)
);

create index if not exists fragments_release_level_idx
  on lskills.fragments (release_id, disclosure_level);

-- ---------------------------------------------------------------------------
-- tools — tool descriptors bound to releases
-- ---------------------------------------------------------------------------
create table if not exists lskills.tools (
  tool_row_id uuid primary key default gen_random_uuid(),
  release_id uuid not null references lskills.releases(release_id) on delete cascade,
  tool_id text not null,
  tool_version text not null default '1.0.0',
  placement text not null default 'packaged',
  descriptor_hash text not null,
  descriptor jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint tools_release_tool_uniq unique (release_id, tool_id, tool_version),
  constraint tools_hash_nonempty check (length(btrim(descriptor_hash)) > 0)
);

create index if not exists tools_tool_id_idx on lskills.tools (tool_id);

-- ---------------------------------------------------------------------------
-- execution_profiles — certified runtime profiles
-- ---------------------------------------------------------------------------
create table if not exists lskills.execution_profiles (
  profile_id uuid primary key default gen_random_uuid(),
  profile_key text not null,
  profile_hash text not null,
  runtime text not null,
  adapter_version text,
  toolchain jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  constraint execution_profiles_key_uniq unique (profile_key),
  constraint execution_profiles_hash_nonempty check (length(btrim(profile_hash)) > 0)
);

-- ---------------------------------------------------------------------------
-- certifications — evidence-backed certification receipts
-- ---------------------------------------------------------------------------
create table if not exists lskills.certifications (
  certification_id uuid primary key default gen_random_uuid(),
  release_id uuid not null references lskills.releases(release_id) on delete cascade,
  profile_id uuid not null references lskills.execution_profiles(profile_id),
  eval_run_ref text,
  evidence_hash text not null,
  state lskills.certification_state not null default 'eval_pending',
  certified_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  constraint certifications_release_profile_uniq unique (release_id, profile_id),
  constraint certifications_evidence_nonempty check (length(btrim(evidence_hash)) > 0)
);

create index if not exists certifications_release_id_idx
  on lskills.certifications (release_id);

-- ---------------------------------------------------------------------------
-- skill_runs — actor-bound run lifecycle
-- ---------------------------------------------------------------------------
create table if not exists lskills.skill_runs (
  run_id uuid primary key default gen_random_uuid(),
  release_id uuid references lskills.releases(release_id) on delete set null,
  skill_id text not null,
  version text not null,
  release_hash text,
  profile_hash text,
  actor_id text not null,
  org_id text not null,
  status lskills.run_status not null default 'started',
  idempotency_key text,
  outcome jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint skill_runs_actor_idempotency_uniq unique (actor_id, idempotency_key)
);

create index if not exists skill_runs_skill_id_idx on lskills.skill_runs (skill_id);
create index if not exists skill_runs_actor_id_idx on lskills.skill_runs (actor_id);

-- ---------------------------------------------------------------------------
-- run_events — ordered event spine for a run
-- ---------------------------------------------------------------------------
create table if not exists lskills.run_events (
  event_id uuid primary key default gen_random_uuid(),
  run_id uuid not null references lskills.skill_runs(run_id) on delete cascade,
  seq bigint generated by default as identity,
  event_type text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists run_events_run_id_seq_idx on lskills.run_events (run_id, seq);

-- ---------------------------------------------------------------------------
-- feedback — corrections / ratings / friction
-- ---------------------------------------------------------------------------
create table if not exists lskills.feedback (
  feedback_id uuid primary key default gen_random_uuid(),
  run_id uuid references lskills.skill_runs(run_id) on delete set null,
  skill_id text,
  actor_id text not null,
  org_id text not null,
  kind lskills.feedback_kind not null default 'other',
  rating numeric,
  friction text,
  missing_step text,
  outcome text,
  notes text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists feedback_skill_id_idx on lskills.feedback (skill_id);
create index if not exists feedback_run_id_idx on lskills.feedback (run_id);

-- ---------------------------------------------------------------------------
-- trace_to_eval_candidates — failed/corrected run → eval queue
-- ---------------------------------------------------------------------------
create table if not exists lskills.trace_to_eval_candidates (
  candidate_id uuid primary key default gen_random_uuid(),
  fingerprint text not null,
  run_id uuid references lskills.skill_runs(run_id) on delete set null,
  skill_id text,
  actor_id text not null,
  org_id text not null,
  summary text,
  observed jsonb not null default '{}'::jsonb,
  status lskills.trace_candidate_status not null default 'queued',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint trace_candidates_fingerprint_uniq unique (fingerprint)
);

create index if not exists trace_candidates_status_idx
  on lskills.trace_to_eval_candidates (status);

-- ---------------------------------------------------------------------------
-- Grants (least privilege; mirrors catalog_core role set)
-- NOTE: roles may already exist from 20260715_000002; create if missing.
-- ---------------------------------------------------------------------------
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'svc_lskills_runtime') then
    create role svc_lskills_runtime nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'svc_lskills_librarian') then
    create role svc_lskills_librarian nologin;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'svc_observer') then
    create role svc_observer nologin;
  end if;
end $$;

grant usage on schema lskills to svc_lskills_runtime, svc_lskills_librarian, svc_observer;

-- Runtime: read registry; write runs/events/feedback/trace candidates.
grant select on lskills.releases, lskills.bundles, lskills.fragments,
  lskills.tools, lskills.execution_profiles, lskills.certifications
  to svc_lskills_runtime;
grant select, insert, update on lskills.skill_runs to svc_lskills_runtime;
grant select, insert on lskills.run_events, lskills.feedback,
  lskills.trace_to_eval_candidates to svc_lskills_runtime;

-- Librarian: curation writes on registry + read telemetry surfaces.
grant select, insert, update on lskills.releases, lskills.bundles, lskills.fragments,
  lskills.tools, lskills.execution_profiles, lskills.certifications
  to svc_lskills_librarian;
grant select on lskills.skill_runs, lskills.run_events, lskills.feedback,
  lskills.trace_to_eval_candidates to svc_lskills_librarian;
grant update on lskills.trace_to_eval_candidates to svc_lskills_librarian;

-- Observer: read-only.
grant select on lskills.releases, lskills.bundles, lskills.fragments,
  lskills.tools, lskills.execution_profiles, lskills.certifications,
  lskills.skill_runs, lskills.run_events, lskills.feedback,
  lskills.trace_to_eval_candidates to svc_observer;

-- ---------------------------------------------------------------------------
-- RLS stubs — enabled; role-scoped policies (global/internal data plane).
-- Org-scoped hardening remains deferred (same posture as catalog_core).
-- ---------------------------------------------------------------------------
alter table lskills.releases enable row level security;
alter table lskills.bundles enable row level security;
alter table lskills.fragments enable row level security;
alter table lskills.tools enable row level security;
alter table lskills.execution_profiles enable row level security;
alter table lskills.certifications enable row level security;
alter table lskills.skill_runs enable row level security;
alter table lskills.run_events enable row level security;
alter table lskills.feedback enable row level security;
alter table lskills.trace_to_eval_candidates enable row level security;

-- Helper macro-style policies: runtime read/write where granted; librarian all;
-- observer read. Drop/create for idempotent re-apply in review environments.

drop policy if exists lskills_releases_runtime_read on lskills.releases;
create policy lskills_releases_runtime_read on lskills.releases
  for select to svc_lskills_runtime using (true);
drop policy if exists lskills_releases_librarian_all on lskills.releases;
create policy lskills_releases_librarian_all on lskills.releases
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_releases_observer_read on lskills.releases;
create policy lskills_releases_observer_read on lskills.releases
  for select to svc_observer using (true);

drop policy if exists lskills_bundles_runtime_read on lskills.bundles;
create policy lskills_bundles_runtime_read on lskills.bundles
  for select to svc_lskills_runtime using (true);
drop policy if exists lskills_bundles_librarian_all on lskills.bundles;
create policy lskills_bundles_librarian_all on lskills.bundles
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_bundles_observer_read on lskills.bundles;
create policy lskills_bundles_observer_read on lskills.bundles
  for select to svc_observer using (true);

drop policy if exists lskills_fragments_runtime_read on lskills.fragments;
create policy lskills_fragments_runtime_read on lskills.fragments
  for select to svc_lskills_runtime using (true);
drop policy if exists lskills_fragments_librarian_all on lskills.fragments;
create policy lskills_fragments_librarian_all on lskills.fragments
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_fragments_observer_read on lskills.fragments;
create policy lskills_fragments_observer_read on lskills.fragments
  for select to svc_observer using (true);

drop policy if exists lskills_tools_runtime_read on lskills.tools;
create policy lskills_tools_runtime_read on lskills.tools
  for select to svc_lskills_runtime using (true);
drop policy if exists lskills_tools_librarian_all on lskills.tools;
create policy lskills_tools_librarian_all on lskills.tools
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_tools_observer_read on lskills.tools;
create policy lskills_tools_observer_read on lskills.tools
  for select to svc_observer using (true);

drop policy if exists lskills_execution_profiles_runtime_read on lskills.execution_profiles;
create policy lskills_execution_profiles_runtime_read on lskills.execution_profiles
  for select to svc_lskills_runtime using (true);
drop policy if exists lskills_execution_profiles_librarian_all on lskills.execution_profiles;
create policy lskills_execution_profiles_librarian_all on lskills.execution_profiles
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_execution_profiles_observer_read on lskills.execution_profiles;
create policy lskills_execution_profiles_observer_read on lskills.execution_profiles
  for select to svc_observer using (true);

drop policy if exists lskills_certifications_runtime_read on lskills.certifications;
create policy lskills_certifications_runtime_read on lskills.certifications
  for select to svc_lskills_runtime using (true);
drop policy if exists lskills_certifications_librarian_all on lskills.certifications;
create policy lskills_certifications_librarian_all on lskills.certifications
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_certifications_observer_read on lskills.certifications;
create policy lskills_certifications_observer_read on lskills.certifications
  for select to svc_observer using (true);

drop policy if exists lskills_skill_runs_runtime_all on lskills.skill_runs;
create policy lskills_skill_runs_runtime_all on lskills.skill_runs
  for all to svc_lskills_runtime using (true) with check (true);
drop policy if exists lskills_skill_runs_librarian_read on lskills.skill_runs;
create policy lskills_skill_runs_librarian_read on lskills.skill_runs
  for select to svc_lskills_librarian using (true);
drop policy if exists lskills_skill_runs_observer_read on lskills.skill_runs;
create policy lskills_skill_runs_observer_read on lskills.skill_runs
  for select to svc_observer using (true);

drop policy if exists lskills_run_events_runtime_all on lskills.run_events;
create policy lskills_run_events_runtime_all on lskills.run_events
  for all to svc_lskills_runtime using (true) with check (true);
drop policy if exists lskills_run_events_librarian_read on lskills.run_events;
create policy lskills_run_events_librarian_read on lskills.run_events
  for select to svc_lskills_librarian using (true);
drop policy if exists lskills_run_events_observer_read on lskills.run_events;
create policy lskills_run_events_observer_read on lskills.run_events
  for select to svc_observer using (true);

drop policy if exists lskills_feedback_runtime_all on lskills.feedback;
create policy lskills_feedback_runtime_all on lskills.feedback
  for all to svc_lskills_runtime using (true) with check (true);
drop policy if exists lskills_feedback_librarian_read on lskills.feedback;
create policy lskills_feedback_librarian_read on lskills.feedback
  for select to svc_lskills_librarian using (true);
drop policy if exists lskills_feedback_observer_read on lskills.feedback;
create policy lskills_feedback_observer_read on lskills.feedback
  for select to svc_observer using (true);

drop policy if exists lskills_trace_runtime_all on lskills.trace_to_eval_candidates;
create policy lskills_trace_runtime_all on lskills.trace_to_eval_candidates
  for all to svc_lskills_runtime using (true) with check (true);
drop policy if exists lskills_trace_librarian_all on lskills.trace_to_eval_candidates;
create policy lskills_trace_librarian_all on lskills.trace_to_eval_candidates
  for all to svc_lskills_librarian using (true) with check (true);
drop policy if exists lskills_trace_observer_read on lskills.trace_to_eval_candidates;
create policy lskills_trace_observer_read on lskills.trace_to_eval_candidates
  for select to svc_observer using (true);

-- verification helpers (safe SELECT-only)
select table_name
from information_schema.tables
where table_schema = 'lskills'
  and table_name in (
    'releases', 'bundles', 'fragments', 'tools', 'execution_profiles',
    'certifications', 'skill_runs', 'run_events', 'feedback',
    'trace_to_eval_candidates'
  )
order by table_name;

-- ---------------------------------------------------------------------------
-- DOWN-MIGRATION: intentionally NOT in this file.
-- If needed, create a separately dated *_down.sql that drops ONLY these
-- additive tables — never drop lskills.catalog / telemetry / eval_runs here.
-- ---------------------------------------------------------------------------
