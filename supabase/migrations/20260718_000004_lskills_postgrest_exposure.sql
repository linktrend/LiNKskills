-- migrate:up
-- Expose lskills to PostgREST (service_role) so consumer telemetry writers and
-- the Librarian Supabase client can reach catalog/telemetry/eval_runs.
--
-- Context: 000002 created least-privilege svc_lskills_* roles for future
-- impersonation, but the studio's current trusted writers use the Supabase
-- service_role key via PostgREST. Without USAGE + table grants AND without
-- listing `lskills` in pgrst.db_schemas, inserts fail with PGRST106
-- ("Invalid schema: lskills").
--
-- This migration is additive and idempotent. It does not weaken RLS for anon /
-- authenticated (no grants to those roles). service_role bypasses RLS in
-- Supabase by design — same posture as other Program writers.

grant usage on schema lskills to service_role;

grant select, insert, update on lskills.catalog to service_role;
grant select, insert on lskills.telemetry to service_role;
grant select, insert on lskills.eval_runs to service_role;

-- Ensure future tables in lskills inherit service_role access for writers.
alter default privileges in schema lskills
  grant select, insert, update on tables to service_role;

-- Expose Program schemas to PostgREST. Keep public + graphql_public; add the
-- studio schemas that already exist on the shared platform project.
do $$
declare
  current_schemas text;
  desired text := 'public, graphql_public, platform, lskills, lbrain, lautowork';
begin
  begin
    current_schemas := current_setting('pgrst.db_schemas', true);
  exception when others then
    current_schemas := null;
  end;

  -- Only widen; never shrink an already-custom list if an operator set more.
  if current_schemas is null or btrim(current_schemas) = '' then
    execute format('alter role authenticator set pgrst.db_schemas to %L', desired);
  elsif position('lskills' in current_schemas) = 0 then
    execute format(
      'alter role authenticator set pgrst.db_schemas to %L',
      current_schemas || ', lskills'
    );
  end if;
end $$;

notify pgrst, 'reload config';
notify pgrst, 'reload schema';
