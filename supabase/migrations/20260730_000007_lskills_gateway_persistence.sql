-- migrate:up
-- LiNKskills gateway durable persistence surfaces — v0.1 (additive)
--
-- ADDITIVE ONLY. Extends `lskills` registry foundation
-- (20260727_000005 / 20260728_000006). Does NOT drop or rewrite
-- existing catalog / telemetry / eval_runs / registry tables.
--
-- Adds GatewayStore parity tables for idempotency + side-effect fencing,
-- optional embedded run event/feedback JSON columns, and a free-form
-- gateway_events spine used by append_event when no run_id is present.
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.
-- This file is authored in LiNKskills for review/handoff; do not apply
-- from a Skills agent session to stage/prod.
--
-- Prerequisite: 20260727_000005_lskills_registry_foundation.sql (+ 000006 RLS).

create extension if not exists "pgcrypto";

create schema if not exists lskills;

-- ---------------------------------------------------------------------------
-- Additive columns on skill_runs for GatewayStore Protocol parity
-- (SQLite embeds events/feedback JSON on the run row).
-- ---------------------------------------------------------------------------
alter table lskills.skill_runs
  add column if not exists events_json jsonb not null default '[]'::jsonb;

alter table lskills.skill_runs
  add column if not exists feedback_json jsonb not null default '[]'::jsonb;

-- ---------------------------------------------------------------------------
-- idempotency — reserve / replay / conflict / fence semantics
-- ---------------------------------------------------------------------------
create table if not exists lskills.idempotency (
  actor_id text not null,
  org_id text not null default '',
  operation text not null,
  idempotency_key text not null,
  request_hash text not null default '',
  status text not null default 'completed',
  envelope jsonb,
  lease_expires_at timestamptz,
  fence_token text,
  fence_generation integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (actor_id, operation, idempotency_key),
  constraint idempotency_status_check check (
    status in ('reserved', 'completed')
  )
);

create index if not exists idempotency_org_actor_idx
  on lskills.idempotency (org_id, actor_id);

-- ---------------------------------------------------------------------------
-- side_effect_intents — durable downstream intent + result fencing
-- ---------------------------------------------------------------------------
create table if not exists lskills.side_effect_intents (
  actor_id text not null,
  org_id text not null default '',
  operation text not null,
  idempotency_key text not null,
  fence_token text not null,
  request_hash text not null,
  downstream_key text not null,
  status text not null,
  result jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (actor_id, operation, idempotency_key),
  constraint side_effect_status_check check (
    status in ('intent', 'result')
  )
);

create index if not exists side_effect_intents_org_actor_idx
  on lskills.side_effect_intents (org_id, actor_id);

-- ---------------------------------------------------------------------------
-- gateway_events — free-form telemetry spine (append_event)
-- ---------------------------------------------------------------------------
create table if not exists lskills.gateway_events (
  event_id bigserial primary key,
  actor_id text,
  org_id text,
  run_id uuid,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists gateway_events_org_actor_idx
  on lskills.gateway_events (org_id, actor_id);
create index if not exists gateway_events_run_id_idx
  on lskills.gateway_events (run_id);

-- ---------------------------------------------------------------------------
-- Grants (runtime write; librarian/observer read)
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

grant select, insert, update on lskills.idempotency to svc_lskills_runtime;
grant select, insert, update on lskills.side_effect_intents to svc_lskills_runtime;
grant select, insert on lskills.gateway_events to svc_lskills_runtime;
grant usage, select on sequence lskills.gateway_events_event_id_seq to svc_lskills_runtime;

grant select on lskills.idempotency, lskills.side_effect_intents, lskills.gateway_events
  to svc_lskills_librarian, svc_observer;

-- ---------------------------------------------------------------------------
-- RLS — transaction-local actor/org GUC identity (same helpers as 000005/000006)
--   SET LOCAL app.current_actor_id = '<actor>';
--   SET LOCAL app.current_org_id = '<org>';
-- ---------------------------------------------------------------------------
alter table lskills.idempotency enable row level security;
alter table lskills.side_effect_intents enable row level security;
alter table lskills.gateway_events enable row level security;

drop policy if exists lskills_idempotency_runtime_all on lskills.idempotency;
create policy lskills_idempotency_runtime_all on lskills.idempotency
  for all to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_idempotency_librarian_read on lskills.idempotency;
create policy lskills_idempotency_librarian_read on lskills.idempotency
  for select to svc_lskills_librarian using (lskills.org_matches(org_id));

drop policy if exists lskills_idempotency_observer_read on lskills.idempotency;
create policy lskills_idempotency_observer_read on lskills.idempotency
  for select to svc_observer using (lskills.org_matches(org_id));

drop policy if exists lskills_side_effect_runtime_all on lskills.side_effect_intents;
create policy lskills_side_effect_runtime_all on lskills.side_effect_intents
  for all to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_side_effect_librarian_read on lskills.side_effect_intents;
create policy lskills_side_effect_librarian_read on lskills.side_effect_intents
  for select to svc_lskills_librarian using (lskills.org_matches(org_id));

drop policy if exists lskills_side_effect_observer_read on lskills.side_effect_intents;
create policy lskills_side_effect_observer_read on lskills.side_effect_intents
  for select to svc_observer using (lskills.org_matches(org_id));

drop policy if exists lskills_gateway_events_runtime_all on lskills.gateway_events;
create policy lskills_gateway_events_runtime_all on lskills.gateway_events
  for all to svc_lskills_runtime
  using (
    (org_id is null and actor_id is null)
    or (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  )
  with check (
    (org_id is null and actor_id is null)
    or (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  );

drop policy if exists lskills_gateway_events_librarian_read on lskills.gateway_events;
create policy lskills_gateway_events_librarian_read on lskills.gateway_events
  for select to svc_lskills_librarian
  using (org_id is null or lskills.org_matches(org_id));

drop policy if exists lskills_gateway_events_observer_read on lskills.gateway_events;
create policy lskills_gateway_events_observer_read on lskills.gateway_events
  for select to svc_observer
  using (org_id is null or lskills.org_matches(org_id));

-- verification helpers (safe SELECT-only)
select table_name
from information_schema.tables
where table_schema = 'lskills'
  and table_name in (
    'idempotency', 'side_effect_intents', 'gateway_events'
  )
order by table_name;

-- ---------------------------------------------------------------------------
-- DOWN-MIGRATION: intentionally NOT in this file.
-- If needed, create a separately dated *_down.sql that drops ONLY these
-- additive tables/columns — never drop lskills schema or prior registry tables.
-- ---------------------------------------------------------------------------
