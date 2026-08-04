-- migrate:up
-- LiNKskills Librarian review_queue — v0.1 (additive)
--
-- ADDITIVE ONLY. Extends `lskills` registry + gateway persistence
-- (20260727_000005 / 20260728_000006 / 20260730_000007). Does NOT drop
-- or rewrite existing catalog / telemetry / registry / gateway tables.
--
-- Provides durable Librarian review queue with tenant/actor RLS,
-- lifecycle states, idempotency keys, provenance, retry/dead-letter,
-- retention, and indexes.
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.
-- This file is authored in LiNKskills for review/handoff; do not apply
-- from a Skills agent session to stage/prod.
--
-- Prerequisite: 20260730_000007_lskills_gateway_persistence.sql
--   (roles svc_lskills_runtime / svc_lskills_librarian / svc_observer,
--    and lskills.org_matches / actor_matches helpers from 000006).

create extension if not exists "pgcrypto";

create schema if not exists lskills;

-- ---------------------------------------------------------------------------
-- Lifecycle enum (idempotent)
-- ---------------------------------------------------------------------------
do $$
begin
  if not exists (
    select 1 from pg_type
    where typname = 'review_queue_status'
      and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.review_queue_status as enum (
      'queued',
      'claimed',
      'in_progress',
      'completed',
      'failed',
      'dead_letter',
      'cancelled',
      'expired'
    );
  end if;
end $$;

-- ---------------------------------------------------------------------------
-- review_queue
-- ---------------------------------------------------------------------------
create table if not exists lskills.review_queue (
  review_id text primary key,
  org_id text not null,
  actor_id text not null,
  kind text not null default 'general',
  status lskills.review_queue_status not null default 'queued',
  payload jsonb not null default '{}'::jsonb,
  provenance jsonb not null default '{}'::jsonb,
  idempotency_key text,
  request_hash text not null default '',
  attempt_count integer not null default 0,
  max_attempts integer not null default 5,
  next_attempt_at timestamptz,
  last_error text,
  dead_letter_reason text,
  claimed_by text,
  claimed_at timestamptz,
  lease_expires_at timestamptz,
  retain_until timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  constraint review_queue_attempts_check check (
    attempt_count >= 0 and max_attempts >= 1 and attempt_count <= max_attempts + 1
  ),
  constraint review_queue_dead_letter_check check (
    status <> 'dead_letter'::lskills.review_queue_status
    or dead_letter_reason is not null
  )
);

-- Idempotency: one active key per org+actor (null keys unrestricted).
create unique index if not exists review_queue_idempotency_uidx
  on lskills.review_queue (org_id, actor_id, idempotency_key)
  where idempotency_key is not null;

create index if not exists review_queue_status_created_idx
  on lskills.review_queue (status, created_at);

create index if not exists review_queue_org_actor_idx
  on lskills.review_queue (org_id, actor_id);

create index if not exists review_queue_org_status_idx
  on lskills.review_queue (org_id, status, next_attempt_at);

create index if not exists review_queue_lease_idx
  on lskills.review_queue (lease_expires_at)
  where status in (
    'claimed'::lskills.review_queue_status,
    'in_progress'::lskills.review_queue_status
  );

create index if not exists review_queue_retention_idx
  on lskills.review_queue (retain_until)
  where retain_until is not null;

create index if not exists review_queue_dead_letter_idx
  on lskills.review_queue (org_id, created_at)
  where status = 'dead_letter'::lskills.review_queue_status;

-- ---------------------------------------------------------------------------
-- Roles (idempotent; created by prior migrations)
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

-- Librarian owns queue write lifecycle; runtime may enqueue; observer read-only.
grant select, insert, update on lskills.review_queue to svc_lskills_librarian;
grant select, insert on lskills.review_queue to svc_lskills_runtime;
grant select on lskills.review_queue to svc_observer;

-- ---------------------------------------------------------------------------
-- RLS — transaction-local actor/org GUC identity
--   SET LOCAL ROLE svc_lskills_librarian;
--   select set_config('app.current_actor_id', '<actor>', true);
--   select set_config('app.current_org_id', '<org>', true);
-- ---------------------------------------------------------------------------
alter table lskills.review_queue enable row level security;

drop policy if exists lskills_review_queue_librarian_all on lskills.review_queue;
create policy lskills_review_queue_librarian_all on lskills.review_queue
  for all to svc_lskills_librarian
  using (lskills.org_matches(org_id))
  with check (lskills.org_matches(org_id));

drop policy if exists lskills_review_queue_runtime_insert on lskills.review_queue;
create policy lskills_review_queue_runtime_insert on lskills.review_queue
  for insert to svc_lskills_runtime
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_review_queue_runtime_select on lskills.review_queue;
create policy lskills_review_queue_runtime_select on lskills.review_queue
  for select to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_review_queue_observer_read on lskills.review_queue;
create policy lskills_review_queue_observer_read on lskills.review_queue
  for select to svc_observer
  using (lskills.org_matches(org_id));

-- verification helpers (safe SELECT-only)
select table_name
from information_schema.tables
where table_schema = 'lskills'
  and table_name = 'review_queue'
order by table_name;

-- ---------------------------------------------------------------------------
-- DOWN-MIGRATION: intentionally NOT in this file.
-- If needed, create a separately dated *_down.sql that drops ONLY
-- lskills.review_queue (+ enum) — never drop lskills schema or prior tables.
-- ---------------------------------------------------------------------------
