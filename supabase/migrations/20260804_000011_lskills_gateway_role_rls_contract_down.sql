-- migrate:down
-- Companion rollback for 20260804_000011_lskills_gateway_role_rls_contract.sql
--
-- Restores the 000007 gateway_events runtime policy (including the historical
-- null/null branch) and revokes runtime membership from svc_lskills_gateway.
-- Does NOT drop svc_lskills_gateway (Platform may own a LOGIN principal).
-- Does NOT drop svc_lskills_runtime or rewrite other 000007 policies.
--
-- IMPORTANT: LiNKplatform alone applies live shared migrations.

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

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'svc_lskills_gateway')
     and exists (select 1 from pg_roles where rolname = 'svc_lskills_runtime') then
    execute 'revoke svc_lskills_runtime from svc_lskills_gateway';
  end if;
end $$;
