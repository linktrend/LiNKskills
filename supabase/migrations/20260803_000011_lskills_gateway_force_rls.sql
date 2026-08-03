-- migrate:up
-- LiNKskills gateway persistence FORCE ROW LEVEL SECURITY — additive
--
-- ADDITIVE ONLY. Does NOT rewrite 20260730_000007 policies or grants.
-- Forces RLS even for table owners so a privileged migration/apply role
-- cannot silently bypass tenant policies when used as a runtime DSN.
--
-- Runtime contract (unchanged from 000006/000007):
--   SET LOCAL ROLE svc_lskills_runtime;
--   select set_config('app.current_actor_id', '<actor>', true);
--   select set_config('app.current_org_id', '<org>', true);
-- Platform must GRANT svc_lskills_runtime TO <stage_login_role> so SET LOCAL
-- ROLE succeeds for the Gateway DSN principal. This migration does not create
-- login roles or bypass RLS.
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.
-- This file is authored in LiNKskills for review/handoff; do not apply
-- from a Skills agent session to stage/prod.
--
-- Prerequisite: 20260730_000007_lskills_gateway_persistence.sql

alter table lskills.idempotency force row level security;
alter table lskills.side_effect_intents force row level security;
alter table lskills.gateway_events force row level security;
alter table lskills.skill_runs force row level security;
alter table lskills.run_events force row level security;
alter table lskills.feedback force row level security;
alter table lskills.trace_to_eval_candidates force row level security;

-- verification helpers (safe SELECT-only)
select c.relname as table_name, c.relrowsecurity as rls, c.relforcerowsecurity as force_rls
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
