-- migrate:down
-- Companion down for 20260803_000011_lskills_gateway_force_rls.sql
--
-- Relaxes FORCE RLS only — leaves ENABLE RLS and all policies intact.
-- Never drop schema, tables, or policies from 000005–000007.
-- Live apply / rollback authority: LiNKplatform alone.

alter table lskills.idempotency no force row level security;
alter table lskills.side_effect_intents no force row level security;
alter table lskills.gateway_events no force row level security;
alter table lskills.skill_runs no force row level security;
alter table lskills.run_events no force row level security;
alter table lskills.feedback no force row level security;
alter table lskills.trace_to_eval_candidates no force row level security;
