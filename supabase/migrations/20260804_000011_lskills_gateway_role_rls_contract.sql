-- migrate:up
-- LiNKskills gateway DSN role + governed-write RLS contract — v0.1 (additive)
--
-- ADDITIVE ONLY. Does NOT rewrite 20260730_000007 table DDL or weaken
-- actor/org WITH CHECK predicates. Extends the runtime contract so stage's
-- svc_lskills_gateway login can assume svc_lskills_runtime under RLS.
--
-- Observed stage defect: PACI skills_list (file catalog) succeeds while
-- skills_run_start INSERT into lskills.idempotency fails with
-- InsufficientPrivilege / RLS policy violation when the Gateway DSN role
-- lacks runtime membership and/or transaction-local actor/org GUCs.
--
-- Runtime contract (unchanged helpers from 000006):
--   SET LOCAL ROLE svc_lskills_runtime;
--   select set_config('app.current_actor_id', '<paci-actor>', true);
--   select set_config('app.current_org_id', '<paci-org>', true);
--
-- This migration:
--   1) Ensures svc_lskills_gateway exists as NOLOGIN / NOBYPASSRLS when absent
--      (Platform may already own a LOGIN principal with the same name — skip create).
--   2) GRANT svc_lskills_runtime TO svc_lskills_gateway so SET LOCAL ROLE works.
--   3) Tightens lskills.gateway_events runtime WITH CHECK to require actor+org
--      (closes the null/null anonymous branch left from 000007; code already
--      fail-closes anonymous append_event).
--
-- Does NOT: FORCE RLS, SECURITY DEFINER, BYPASSRLS, disable RLS, PUBLIC grants,
-- hardcoded stage actor/org IDs, or table-privilege grants to the gateway role
-- (writes remain via SET LOCAL ROLE → svc_lskills_runtime grants).
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.
-- This file is authored in LiNKskills for review/handoff; do not apply
-- from a Skills agent session to stage/prod.
--
-- Prerequisite: 20260730_000007_lskills_gateway_persistence.sql (+ 000006 helpers).

create extension if not exists "pgcrypto";

create schema if not exists lskills;

-- ---------------------------------------------------------------------------
-- Roles: gateway DSN group + runtime membership (SET LOCAL ROLE contract)
-- ---------------------------------------------------------------------------
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'svc_lskills_runtime') then
    create role svc_lskills_runtime nologin nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'svc_lskills_gateway') then
    -- NOLOGIN group/principal placeholder. Platform may instead create a LOGIN
    -- role with this name before apply; IF NOT EXISTS preserves that LOGIN.
    create role svc_lskills_gateway nologin nobypassrls;
  end if;
end $$;

-- Membership is idempotent. Enables:
--   SET LOCAL ROLE svc_lskills_runtime
-- from a session whose SESSION_USER is svc_lskills_gateway (or a login that
-- inherits this role). Does not grant BYPASSRLS or widen WITH CHECK.
grant svc_lskills_runtime to svc_lskills_gateway;

-- ---------------------------------------------------------------------------
-- gateway_events — drop anonymous null/null WITH CHECK branch (fail closed)
-- ---------------------------------------------------------------------------
drop policy if exists lskills_gateway_events_runtime_all on lskills.gateway_events;
create policy lskills_gateway_events_runtime_all on lskills.gateway_events
  for all to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

-- verification helpers (safe SELECT-only)
select
  r.rolname,
  r.rolcanlogin,
  r.rolbypassrls,
  exists (
    select 1
    from pg_auth_members m
    join pg_roles g on g.oid = m.roleid
    where m.member = r.oid and g.rolname = 'svc_lskills_runtime'
  ) as has_runtime_membership
from pg_roles r
where r.rolname in ('svc_lskills_gateway', 'svc_lskills_runtime')
order by r.rolname;

select c.relname as table_name, c.relrowsecurity as rls
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'lskills'
  and c.relkind = 'r'
  and c.relname in (
    'idempotency',
    'side_effect_intents',
    'gateway_events',
    'skill_runs',
    'run_events',
    'feedback',
    'trace_to_eval_candidates'
  )
order by 1;

-- ---------------------------------------------------------------------------
-- DOWN-MIGRATION: companion 20260804_000011_lskills_gateway_role_rls_contract_down.sql
-- ---------------------------------------------------------------------------
