-- LiNKskills Logic Engine PRD v4.0 RLS policies

alter table tenants enable row level security;
alter table principals enable row level security;
alter table api_keys enable row level security;
alter table capabilities enable row level security;
alter table capability_versions enable row level security;
alter table packages enable row level security;
alter table dpr_registry enable row level security;
alter table complexity_multipliers enable row level security;
alter table class_b_entitlements enable row level security;
alter table override_approvals enable row level security;
alter table runs enable row level security;
alter table idempotency_records enable row level security;
alter table disclosures enable row level security;
alter table receipts enable row level security;
alter table audit_logs enable row level security;
alter table usage_events enable row level security;
alter table security_events enable row level security;
alter table financial_ledger enable row level security;
alter table kill_switch_state enable row level security;
alter table safe_mode_state enable row level security;
alter table alerts enable row level security;

-- Tenant partitioning for shared Supabase project.
-- Assumes tenant_id in JWT claims for interactive access.
-- Service control-plane should use backend role with bypass RLS or dedicated policies.

create policy tenants_tenant_isolation on tenants
  for select using (tenant_id = auth.jwt() ->> 'tenant_id');

create policy principals_tenant_isolation on principals
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy api_keys_tenant_isolation on api_keys
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy capabilities_internal_read on capabilities
  for select using (true);

create policy capability_versions_internal_read on capability_versions
  for select using (true);

create policy packages_internal_read on packages
  for select using (true);

create policy dpr_registry_tenant_isolation on dpr_registry
  for select using (
    tenant_id is null or tenant_id = auth.jwt() ->> 'tenant_id'
  );

create policy complexity_multipliers_internal_read on complexity_multipliers
  for select using (true);

create policy class_b_entitlements_tenant_isolation on class_b_entitlements
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy override_approvals_tenant_isolation on override_approvals
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy runs_tenant_isolation on runs
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy idempotency_tenant_isolation on idempotency_records
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy disclosures_tenant_isolation on disclosures
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy receipts_tenant_isolation on receipts
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy audit_logs_tenant_isolation on audit_logs
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy usage_events_tenant_isolation on usage_events
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy financial_ledger_tenant_isolation on financial_ledger
  for all using (tenant_id = auth.jwt() ->> 'tenant_id')
  with check (tenant_id = auth.jwt() ->> 'tenant_id');

create policy security_events_internal_read on security_events
  for select using (true);

create policy kill_switch_internal_read on kill_switch_state
  for select using (true);

create policy safe_mode_internal_read on safe_mode_state
  for select using (true);

create policy alerts_internal_read on alerts
  for select using (true);
