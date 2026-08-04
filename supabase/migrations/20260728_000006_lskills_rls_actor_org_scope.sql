-- migrate:up
-- LiNKskills registry RLS hardening — actor/org transaction-local GUC scope.
--
-- Upgrades databases that received stub `using (true)` policies from
-- 20260727_000005_lskills_registry_foundation.sql. Fresh installs get the same
-- policies from the corrected foundation file; this migration is idempotent.
--
-- Identity is set per transaction:
--   SET LOCAL app.current_actor_id = '<actor>';
--   SET LOCAL app.current_org_id = '<org>';

-- ---------------------------------------------------------------------------
-- Helpers — transaction-local GUC readers
-- ---------------------------------------------------------------------------
create or replace function lskills.current_actor_id()
returns text
language sql
stable
as $$
  select nullif(current_setting('app.current_actor_id', true), '');
$$;

create or replace function lskills.current_org_id()
returns text
language sql
stable
as $$
  select nullif(current_setting('app.current_org_id', true), '');
$$;

create or replace function lskills.require_org_context()
returns boolean
language sql
stable
as $$
  select lskills.current_org_id() is not null;
$$;

create or replace function lskills.actor_matches(row_actor_id text)
returns boolean
language sql
stable
as $$
  select lskills.current_actor_id() is not null
    and row_actor_id = lskills.current_actor_id();
$$;

create or replace function lskills.org_matches(row_org_id text)
returns boolean
language sql
stable
as $$
  select lskills.current_org_id() is not null
    and row_org_id = lskills.current_org_id();
$$;

create or replace function lskills.run_events_org_match(p_run_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from lskills.skill_runs r
    where r.run_id = p_run_id
      and lskills.org_matches(r.org_id)
  );
$$;

create or replace function lskills.run_events_actor_org_match(p_run_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from lskills.skill_runs r
    where r.run_id = p_run_id
      and lskills.org_matches(r.org_id)
      and lskills.actor_matches(r.actor_id)
  );
$$;

grant execute on function lskills.current_actor_id() to svc_lskills_runtime, svc_lskills_librarian, svc_observer;
grant execute on function lskills.current_org_id() to svc_lskills_runtime, svc_lskills_librarian, svc_observer;
grant execute on function lskills.require_org_context() to svc_lskills_runtime, svc_lskills_librarian, svc_observer;
grant execute on function lskills.actor_matches(text) to svc_lskills_runtime, svc_lskills_librarian, svc_observer;
grant execute on function lskills.org_matches(text) to svc_lskills_runtime, svc_lskills_librarian, svc_observer;
grant execute on function lskills.run_events_org_match(uuid) to svc_lskills_runtime, svc_lskills_librarian, svc_observer;
grant execute on function lskills.run_events_actor_org_match(uuid) to svc_lskills_runtime, svc_lskills_librarian, svc_observer;

-- ---------------------------------------------------------------------------
-- Drop stub policies (true-wide) and recreate scoped policies
-- ---------------------------------------------------------------------------

-- Catalog/registry tables: role-based access requires org context GUC (no per-row org column).
drop policy if exists lskills_releases_runtime_read on lskills.releases;
create policy lskills_releases_runtime_read on lskills.releases
  for select to svc_lskills_runtime
  using (lskills.require_org_context());

drop policy if exists lskills_releases_librarian_all on lskills.releases;
create policy lskills_releases_librarian_all on lskills.releases
  for all to svc_lskills_librarian
  using (lskills.require_org_context())
  with check (lskills.require_org_context());

drop policy if exists lskills_releases_observer_read on lskills.releases;
create policy lskills_releases_observer_read on lskills.releases
  for select to svc_observer
  using (lskills.require_org_context());

drop policy if exists lskills_bundles_runtime_read on lskills.bundles;
create policy lskills_bundles_runtime_read on lskills.bundles
  for select to svc_lskills_runtime
  using (lskills.require_org_context());

drop policy if exists lskills_bundles_librarian_all on lskills.bundles;
create policy lskills_bundles_librarian_all on lskills.bundles
  for all to svc_lskills_librarian
  using (lskills.require_org_context())
  with check (lskills.require_org_context());

drop policy if exists lskills_bundles_observer_read on lskills.bundles;
create policy lskills_bundles_observer_read on lskills.bundles
  for select to svc_observer
  using (lskills.require_org_context());

drop policy if exists lskills_fragments_runtime_read on lskills.fragments;
create policy lskills_fragments_runtime_read on lskills.fragments
  for select to svc_lskills_runtime
  using (lskills.require_org_context());

drop policy if exists lskills_fragments_librarian_all on lskills.fragments;
create policy lskills_fragments_librarian_all on lskills.fragments
  for all to svc_lskills_librarian
  using (lskills.require_org_context())
  with check (lskills.require_org_context());

drop policy if exists lskills_fragments_observer_read on lskills.fragments;
create policy lskills_fragments_observer_read on lskills.fragments
  for select to svc_observer
  using (lskills.require_org_context());

drop policy if exists lskills_tools_runtime_read on lskills.tools;
create policy lskills_tools_runtime_read on lskills.tools
  for select to svc_lskills_runtime
  using (lskills.require_org_context());

drop policy if exists lskills_tools_librarian_all on lskills.tools;
create policy lskills_tools_librarian_all on lskills.tools
  for all to svc_lskills_librarian
  using (lskills.require_org_context())
  with check (lskills.require_org_context());

drop policy if exists lskills_tools_observer_read on lskills.tools;
create policy lskills_tools_observer_read on lskills.tools
  for select to svc_observer
  using (lskills.require_org_context());

drop policy if exists lskills_execution_profiles_runtime_read on lskills.execution_profiles;
create policy lskills_execution_profiles_runtime_read on lskills.execution_profiles
  for select to svc_lskills_runtime
  using (lskills.require_org_context());

drop policy if exists lskills_execution_profiles_librarian_all on lskills.execution_profiles;
create policy lskills_execution_profiles_librarian_all on lskills.execution_profiles
  for all to svc_lskills_librarian
  using (lskills.require_org_context())
  with check (lskills.require_org_context());

drop policy if exists lskills_execution_profiles_observer_read on lskills.execution_profiles;
create policy lskills_execution_profiles_observer_read on lskills.execution_profiles
  for select to svc_observer
  using (lskills.require_org_context());

drop policy if exists lskills_certifications_runtime_read on lskills.certifications;
create policy lskills_certifications_runtime_read on lskills.certifications
  for select to svc_lskills_runtime
  using (lskills.require_org_context());

drop policy if exists lskills_certifications_librarian_all on lskills.certifications;
create policy lskills_certifications_librarian_all on lskills.certifications
  for all to svc_lskills_librarian
  using (lskills.require_org_context())
  with check (lskills.require_org_context());

drop policy if exists lskills_certifications_observer_read on lskills.certifications;
create policy lskills_certifications_observer_read on lskills.certifications
  for select to svc_observer
  using (lskills.require_org_context());

-- Multi-tenant run / feedback / trace tables: org + actor match for runtime writes.
drop policy if exists lskills_skill_runs_runtime_all on lskills.skill_runs;
create policy lskills_skill_runs_runtime_all on lskills.skill_runs
  for all to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_skill_runs_librarian_read on lskills.skill_runs;
create policy lskills_skill_runs_librarian_read on lskills.skill_runs
  for select to svc_lskills_librarian
  using (lskills.org_matches(org_id));

drop policy if exists lskills_skill_runs_observer_read on lskills.skill_runs;
create policy lskills_skill_runs_observer_read on lskills.skill_runs
  for select to svc_observer
  using (lskills.org_matches(org_id));

drop policy if exists lskills_run_events_runtime_all on lskills.run_events;
create policy lskills_run_events_runtime_all on lskills.run_events
  for all to svc_lskills_runtime
  using (lskills.run_events_actor_org_match(run_id))
  with check (lskills.run_events_actor_org_match(run_id));

drop policy if exists lskills_run_events_librarian_read on lskills.run_events;
create policy lskills_run_events_librarian_read on lskills.run_events
  for select to svc_lskills_librarian
  using (lskills.run_events_org_match(run_id));

drop policy if exists lskills_run_events_observer_read on lskills.run_events;
create policy lskills_run_events_observer_read on lskills.run_events
  for select to svc_observer
  using (lskills.run_events_org_match(run_id));

drop policy if exists lskills_feedback_runtime_all on lskills.feedback;
create policy lskills_feedback_runtime_all on lskills.feedback
  for all to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_feedback_librarian_read on lskills.feedback;
create policy lskills_feedback_librarian_read on lskills.feedback
  for select to svc_lskills_librarian
  using (lskills.org_matches(org_id));

drop policy if exists lskills_feedback_observer_read on lskills.feedback;
create policy lskills_feedback_observer_read on lskills.feedback
  for select to svc_observer
  using (lskills.org_matches(org_id));

drop policy if exists lskills_trace_runtime_all on lskills.trace_to_eval_candidates;
create policy lskills_trace_runtime_all on lskills.trace_to_eval_candidates
  for all to svc_lskills_runtime
  using (lskills.org_matches(org_id) and lskills.actor_matches(actor_id))
  with check (lskills.org_matches(org_id) and lskills.actor_matches(actor_id));

drop policy if exists lskills_trace_librarian_all on lskills.trace_to_eval_candidates;
create policy lskills_trace_librarian_all on lskills.trace_to_eval_candidates
  for all to svc_lskills_librarian
  using (lskills.org_matches(org_id))
  with check (lskills.org_matches(org_id));

drop policy if exists lskills_trace_observer_read on lskills.trace_to_eval_candidates;
create policy lskills_trace_observer_read on lskills.trace_to_eval_candidates
  for select to svc_observer
  using (lskills.org_matches(org_id));
