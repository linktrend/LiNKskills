-- LiNKskills Logic Engine PRD v4.0 (MVO Class A) schema

create table if not exists tenants (
  tenant_id text primary key,
  slug text,
  kind text not null default 'internal',
  created_at timestamptz not null default now()
);

create table if not exists principals (
  principal_id text primary key,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  allowed_capabilities text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists api_keys (
  key_id text primary key,
  key_hash text not null unique,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  state text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  rotated_at timestamptz,
  revoked_at timestamptz,
  last_used_at timestamptz
);

create table if not exists capabilities (
  capability_id text not null,
  version text not null,
  source_type text not null,
  lifecycle_state text not null,
  visibility text not null,
  capability_class text not null,
  license_type text not null,
  certification_state text not null,
  activation_state text not null,
  execution_modes jsonb not null,
  disclosure_mode text not null,
  input_schema_ref text,
  output_schema_ref text,
  source_trace jsonb not null,
  active_from timestamptz,
  created_at timestamptz not null default now(),
  primary key (capability_id, version)
);

create table if not exists capability_versions (
  capability_id text not null,
  version text not null,
  certification_state text not null,
  activation_state text not null,
  effective_from timestamptz,
  effective_to timestamptz,
  approved_by text,
  created_at timestamptz not null default now(),
  primary key (capability_id, version),
  foreign key (capability_id, version) references capabilities(capability_id, version) on delete cascade
);

create table if not exists packages (
  package_id text not null,
  version text not null,
  included_capabilities text[] not null,
  step_order text[] not null,
  gates text[] not null,
  policy_profile text not null,
  lifecycle_state text not null,
  visibility text not null,
  created_at timestamptz not null default now(),
  primary key (package_id, version)
);

create table if not exists dpr_registry (
  dpr_id text primary key,
  tenant_id text references tenants(tenant_id) on delete cascade,
  active boolean not null,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists complexity_multipliers (
  capability_id text not null,
  version text not null,
  multiplier numeric(12,6) not null,
  effective_from timestamptz not null,
  effective_to timestamptz,
  proposed_by text not null,
  approved_by text,
  approval_state text not null,
  created_at timestamptz not null default now(),
  primary key (capability_id, version, effective_from)
);

create table if not exists class_b_entitlements (
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  capability_id text not null,
  active boolean not null,
  created_at timestamptz not null default now(),
  primary key (tenant_id, capability_id)
);

create table if not exists override_approvals (
  override_id text primary key,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  capability_id text not null,
  authority_chain text[] not null,
  approved boolean not null,
  emergency boolean not null,
  created_at timestamptz not null default now()
);

create table if not exists runs (
  run_id text primary key,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  capability_id text not null,
  capability_version text not null,
  mission_id text,
  task_id text,
  dpr_id text,
  billing_track text not null,
  venture_id text,
  client_id text,
  status text not null,
  context_refs jsonb not null default '[]'::jsonb,
  output_metadata jsonb not null default '{}'::jsonb,
  diagnostics_redacted jsonb,
  cost_breakdown jsonb,
  started_at timestamptz not null,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists idempotency_records (
  dedupe_scope text primary key,
  endpoint text not null,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  idempotency_key text not null,
  payload_hash text not null,
  response_payload jsonb not null,
  status_code integer not null,
  created_at timestamptz not null,
  expires_at timestamptz not null
);

create table if not exists disclosures (
  disclosure_id text primary key,
  run_id text not null references runs(run_id) on delete cascade,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  step_scope text not null,
  token_jti text not null,
  token_exp timestamptz not null,
  manifest_ref text not null,
  purge_due_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists receipts (
  receipt_id text primary key,
  run_id text not null references runs(run_id) on delete cascade,
  tenant_id text references tenants(tenant_id) on delete cascade,
  result_status text not null,
  policy_summary jsonb not null default '[]'::jsonb,
  retention_class text not null,
  evidence_hashes text[] not null default '{}',
  cost_breakdown jsonb,
  data_purge_status text not null,
  audit_refs text[] not null default '{}',
  purge_due_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists audit_logs (
  event_id text primary key,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  action text not null,
  target_id text not null,
  status text not null,
  details jsonb not null default '{}'::jsonb,
  purge_due_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists usage_events (
  event_id text primary key,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  run_id text,
  service text not null default 'logic-engine',
  action text not null,
  endpoint text not null,
  latency_ms integer not null,
  success boolean not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists security_events (
  event_id text primary key,
  source text not null,
  tenant_id text,
  principal_id text,
  event_type text not null,
  severity text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists financial_ledger (
  entry_id text primary key,
  tenant_id text not null references tenants(tenant_id) on delete cascade,
  run_id text not null references runs(run_id) on delete cascade,
  principal_id text not null references principals(principal_id) on delete cascade,
  capability_id text not null,
  capability_version text not null,
  amount_usd numeric(14,6) not null,
  token_cost_usd numeric(14,6) not null,
  tool_cost_usd numeric(14,6) not null,
  complexity_multiplier numeric(12,6) not null,
  estimated boolean not null,
  track text not null,
  venture_id text,
  client_id text,
  purge_due_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists kill_switch_state (
  id boolean primary key default true,
  level text not null,
  scope_type text not null,
  scope_id text not null,
  reason text not null,
  hard_cancel_inflight boolean not null,
  activated_at timestamptz,
  activated_by text
);

create table if not exists safe_mode_state (
  id boolean primary key default true,
  enabled boolean not null,
  reason text,
  updated_at timestamptz
);

create table if not exists alerts (
  alert_id text primary key,
  message text not null,
  severity text not null default 'warning',
  created_at timestamptz not null default now()
);

create index if not exists idx_principals_tenant on principals(tenant_id);
create index if not exists idx_capabilities_class on capabilities(capability_class, certification_state, activation_state);
create index if not exists idx_runs_tenant on runs(tenant_id);
create index if not exists idx_runs_principal on runs(principal_id);
create index if not exists idx_runs_status on runs(status);
create index if not exists idx_idempotency_expires on idempotency_records(expires_at);
create index if not exists idx_disclosures_run on disclosures(run_id);
create index if not exists idx_disclosures_purge on disclosures(purge_due_at);
create index if not exists idx_receipts_run on receipts(run_id);
create index if not exists idx_receipts_purge on receipts(purge_due_at);
create index if not exists idx_audit_logs_tenant on audit_logs(tenant_id);
create index if not exists idx_audit_logs_purge on audit_logs(purge_due_at);
create index if not exists idx_usage_events_tenant on usage_events(tenant_id);
create index if not exists idx_security_events_created on security_events(created_at);
create index if not exists idx_financial_ledger_tenant on financial_ledger(tenant_id);
create index if not exists idx_financial_ledger_created on financial_ledger(created_at);
create index if not exists idx_financial_ledger_purge on financial_ledger(purge_due_at);
