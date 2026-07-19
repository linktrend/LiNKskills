-- migrate:up
-- LiNKskills catalog + mandatory-eval + telemetry core schema, written fresh
-- against the shared platform foundation. This is the first real migration for
-- LiNKskills; it turns the reviewed design doc into applied schema.
--
-- Context/authority:
--   * LiNKskills/docs/archive/specs/catalog-eval-telemetry-spec.md (this repo -- the full
--     design; §1 catalog, §2 telemetry, §3 eval_runs, §1.1 certification gate)
--   * LiNKskills/docs/adr/0001-retire-logic-engine-governance-layer.md
--     (why LiNKskills is scoped to catalog + eval + telemetry ONLY -- never
--     governance, leases, entitlements, kill-switches, or per-tenant policy)
--   * LiNKplatform/docs/specs/shared-foundation-spec.md §3 (schema-per-Program),
--     §7 (LiNKskills catalog + mandatory-eval schema; "judgment step runs on the
--     same model tier ... never a cheap/fast tier")
--
-- Conventions mirrored from the sibling migrations
-- (LiNKplatform/.../20260714_000001_platform_foundation.sql,
--  LiNKsites/.../20260715_000001_lsites_sites_core.sql,
--  LiNKbrain/.../20260715_000001_lbrain_memory_core.sql):
--   * a real Postgres schema per Program (`lskills`), with PLAIN table names
--     inside it (`lskills.catalog`, `lskills.telemetry`, `lskills.eval_runs`) --
--     NOT underscore-flattened names in `public`. The spec's logical names
--     `lskills_catalog` / `lskills_telemetry` / `lskills_eval_runs` map to these
--     schema-qualified names (spec scope-note; shared-foundation §3);
--   * enum types created idempotently via a `do $$ ... if not exists ... $$` guard;
--   * a dedicated, least-privilege `nologin` runtime role set;
--   * RLS enabled on every table from the start.
--
-- Prerequisite: LiNKplatform/supabase/migrations/20260714_000001_
-- platform_foundation.sql must already be applied to this same database
-- (creates the `platform` schema, `platform.organizations`, and
-- `platform.has_org_access()` referenced below).
--
-- ---------------------------------------------------------------------------
-- ORG-SCOPING DECISION (explicit, per the spec's §2 exclusions + ADR 0001)
-- ---------------------------------------------------------------------------
-- Skills are LiNKtrend's OWN internal library. Every internal agent draws on the
-- same catalog regardless of which client project it happens to be serving --
-- there is no notion of "client A may use skill X but client B may not". That
-- kind of per-tenant, permission-to-act differentiation is exactly the reversed
-- Logic Engine design that ADR 0001 excised, and where it legitimately lives now
-- is `platform.capabilities` / `platform.capability_grants` (external-capability
-- licensing) + each Program's own Ledger -- NOT here. The spec's §2 telemetry
-- table deliberately drops every tenant/entitlement/authorization column for the
-- same reason ("None of these belong to a catalog+telemetry system").
--
-- Conclusion: the catalog/telemetry/eval data is GLOBAL / internal-only. This is
-- the same posture as LiNKbrain's `org_id is null` case (global/internal
-- knowledge shared across all internal agents), so we follow that precedent:
--   * `lskills.catalog` carries a NULLABLE `org_id` (default NULL = global) purely
--     for FUTURE-PROOFING -- if a single skill were ever authored/licensed for one
--     specific org. It carries NO authorization semantics today; nothing reads it
--     to make an access decision, and per-client skill *licensing* (if it ever
--     exists) would still be expressed via platform.capabilities, not by a gate in
--     this schema.
--   * `lskills.telemetry` and `lskills.eval_runs` get NO org_id at all. Telemetry
--     is observational and spec §2 explicitly forbids tenant columns; eval runs are
--     internal quality data. `program_ref` on telemetry is a plain LABEL
--     (e.g. `lsites`, `lsales`), never a tenant/authz key.
--   * RLS is enabled on every table, but NO org-scoped policies are built around
--     `org_id` yet (deferred hardening, mirroring how platform_foundation and
--     lbrain deferred member-facing policies). Only the least-privilege svc_*
--     roles touch these tables for now. If a per-org-licensed skill ever lands,
--     add the org-scoped SELECT policy then -- the nullable column makes that a
--     non-breaking change.

create extension if not exists "pgcrypto";

create schema if not exists lskills;

do $$
begin
  -- Right-sized template profile (spec §5). Drives which structural rules
  -- validator.py enforces; recorded here so catalog + validator agree.
  if not exists (select 1 from pg_type where typname = 'format_profile' and typnamespace = 'lskills'::regnamespace) then
    create type lskills.format_profile as enum ('simple', 'heavy');
  end if;

  -- Certification state: the Librarian's INTERNAL curation/promotion gate
  -- (spec §1.1). Emphatically NOT the old Logic Engine's tenant activation_state
  -- / entitlement, and NOT a Program-execution permission (ADR 0001). Ordered
  -- draft -> eval_pending -> usable, with deprecated as the retirement sink.
  if not exists (select 1 from pg_type where typname = 'certification_state' and typnamespace = 'lskills'::regnamespace) then
    create type lskills.certification_state as enum ('draft', 'eval_pending', 'usable', 'deprecated');
  end if;

  -- Telemetry status, lifted from today's execution_ledger.jsonl `status` values
  -- (spec §2). Observational only -- telemetry never gates anything.
  if not exists (select 1 from pg_type where typname = 'telemetry_status' and typnamespace = 'lskills'::regnamespace) then
    create type lskills.telemetry_status as enum ('initialized', 'in_progress', 'pending_approval', 'completed', 'failed');
  end if;

  -- Model tier that JUDGED an eval run. This enum has NO cheap/fast member on
  -- purpose: shared-foundation §7 requires the judgment step to run on the same
  -- frontier tier as the Programs' real reasoning work, "never a cheap/fast
  -- tier". Mirrors LiNKbrain's `judge_tier` treatment so the rule is a real DB
  -- constraint here too, not a documented convention. (This column is an
  -- addition beyond spec §3's original table; recorded in the spec doc alongside
  -- this migration.)
  if not exists (select 1 from pg_type where typname = 'judge_tier' and typnamespace = 'lskills'::regnamespace) then
    create type lskills.judge_tier as enum ('high', 'frontier');
  end if;
end $$;

-- ---------------------------------------------------------------------------
-- lskills.catalog  (spec §1 "lskills_catalog") -- one row per skill VERSION.
-- Supersedes the flat manifest.json skill entries by adding the eval gate and
-- the certification_state promotion state. PK is (skill_id, version).
-- ---------------------------------------------------------------------------
create table if not exists lskills.catalog (
  skill_id text not null,                              -- stable kebab-case id, matches skills/<skill_id>/
  version text not null,                               -- semver, matches SKILL.md frontmatter `version`
  -- FUTURE-PROOFING ONLY (see ORG-SCOPING DECISION header). NULL = global /
  -- internal skill available to all internal agents. Carries no authz semantics.
  org_id uuid references platform.organizations(id) on delete set null,
  display_name text not null,
  description text,
  format_profile lskills.format_profile not null default 'heavy',  -- spec §5; default heavy = backward compatible
  frontmatter jsonb not null default '{}'::jsonb,      -- parsed SKILL.md frontmatter
  disclosure_refs jsonb not null default '{}'::jsonb,  -- progressive-disclosure file pointers (Golden Template shape)
  -- MANDATORY eval-suite pointer (spec §1, §7). NOT NULL: a catalog row cannot
  -- even EXIST without declaring its baseline eval suite path. The non-empty
  -- CHECK below closes the "empty-string placeholder" loophole that a bare
  -- NOT NULL would leave open.
  eval_suite_ref text not null,
  certification_state lskills.certification_state not null default 'draft',
  min_reasoning_tier text,                             -- denormalized from frontmatter engine.min_reasoning_tier
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint catalog_pkey primary key (skill_id, version),
  -- Loophole close #1: eval_suite_ref may never be an empty/whitespace-only
  -- placeholder for ANY row, in any state.
  constraint catalog_eval_suite_ref_nonempty
    check (length(btrim(eval_suite_ref)) > 0),
  -- Loophole close #2 (the explicit, self-documenting gate the design insists
  -- on -- spec §1): a `usable` row must have a real, path-shaped eval_suite_ref.
  -- Redundant with the NOT NULL + non-empty check today, but stated explicitly so
  -- the gate survives even if NOT NULL is ever relaxed, and so a value like 'tbd'
  -- can never masquerade as an attached suite once a skill is `usable`.
  constraint catalog_usable_requires_eval_suite
    check (
      certification_state <> 'usable'
      or (
        eval_suite_ref is not null
        and length(btrim(eval_suite_ref)) > 0
        and position('/' in eval_suite_ref) > 0
        and eval_suite_ref like '%.yaml'
      )
    )
);

comment on column lskills.catalog.org_id is
  'FUTURE-PROOFING ONLY. NULL = global/internal skill (all internal agents). '
  'No authorization semantics today; per-client skill licensing (if ever) lives '
  'in platform.capabilities, not here. See migration header ORG-SCOPING DECISION.';
comment on column lskills.catalog.eval_suite_ref is
  'Mandatory pointer to the skill''s baseline eval suite (e.g. '
  'skills/<skill_id>/references/eval-suite.yaml). NOT NULL + non-empty CHECK: a '
  'row cannot exist without one. Promotion to `usable` additionally requires a '
  'PASSING eval_run (enforced by the trigger below), so a usable skill is always '
  'backed by a suite that actually passed -- not just a declared path.';
comment on column lskills.catalog.certification_state is
  'Librarian-internal curation gate (spec §1.1). NOT tenant activation/entitlement '
  'and NOT a Program-execution permission (ADR 0001). Only `usable` skills are '
  'surfaced to agents as relied-upon library entries.';

-- ---------------------------------------------------------------------------
-- lskills.eval_runs  (spec §3 "lskills_eval_runs") -- one row per execution of a
-- skill version's eval suite against a candidate build. Records rubric scores
-- PER DIMENSION, not a single pass/fail bit.
--
-- Declared BEFORE lskills.telemetry only for readability; ordering is otherwise
-- irrelevant. It IS declared before the catalog trigger function that reads it.
-- ---------------------------------------------------------------------------
create table if not exists lskills.eval_runs (
  eval_run_id uuid primary key default gen_random_uuid(),
  skill_id text not null,
  skill_version text not null,                         -- candidate version being judged
  eval_suite_ref text not null,                        -- the suite that was run (matches catalog.eval_suite_ref)
  rubric_scores jsonb not null,                        -- per-dimension scores, e.g. {"correctness":0.95,...}
  overall_score numeric,                               -- weighted aggregate of rubric_scores
  passed boolean not null default false,               -- overall >= threshold AND no hard-fail dimension below floor
  pass_threshold numeric,                              -- threshold applied (copied from suite for auditability)
  efficiency_metrics jsonb not null default '{}'::jsonb, -- {tokens_used, duration_ms, tool_calls, disclosure_files_read}
  size_metrics jsonb not null default '{}'::jsonb,     -- {skill_md_lines, total_skill_bytes, context_required}
  judge_model text not null,                           -- model that judged the run, e.g. 'gpt-5'
  judge_model_version text,                            -- pinned model/version string for reproducibility
  -- HARD REQUIREMENT (shared-foundation §7): the judge runs on a frontier tier,
  -- never a cheap/fast model. NOT NULL + an enum with only ('high','frontier')
  -- members makes a cheap-tier eval literally unrepresentable; the CHECK is
  -- belt-and-braces if the enum is ever widened. Mirrors LiNKbrain.
  judge_tier lskills.judge_tier not null,
  -- Comparison against the prior version's eval (spec §3). We use a SELF-
  -- REFERENCING FK to the exact prior run (compared_to_eval_run_id) rather than
  -- relying only on the version string, because a single skill version can have
  -- MANY eval runs -- a bare `compared_to_version` string is ambiguous about
  -- WHICH run the delta was computed against, whereas an FK pins it precisely and
  -- is referential-integrity-backed. `compared_to_version` is kept as a
  -- denormalized convenience (matches spec §3) and for the common case where only
  -- the version label is needed.
  compared_to_eval_run_id uuid references lskills.eval_runs(eval_run_id) on delete set null,
  compared_to_version text,
  delta_vs_previous jsonb,                             -- per-dimension + overall deltas vs the compared run (Librarian's clean-improvement signal)
  created_at timestamptz not null default now(),
  constraint eval_runs_judge_tier_not_cheap check (judge_tier in ('high', 'frontier'))
);

comment on column lskills.eval_runs.compared_to_eval_run_id is
  'Self-referencing FK to the exact prior eval_run this candidate was judged '
  'against. Preferred over a bare version string because one skill version can '
  'have many runs; the FK removes that ambiguity. delta_vs_previous is computed '
  'relative to THIS run.';
comment on column lskills.eval_runs.judge_tier is
  'Frontier-only by doctrine (shared-foundation §7). Cheap/fast tiers are '
  'unrepresentable (enum has no such member) and additionally rejected by the '
  'CHECK constraint.';

-- ---------------------------------------------------------------------------
-- lskills.telemetry  (spec §2 "lskills_telemetry") -- every real invocation of a
-- skill. Extends the intent of today's execution_ledger.jsonl with the fields
-- the audit flagged as missing. Field NAMES borrowed from the archived Logic
-- Engine runs/usage_events tables where sensible -- DELIBERATELY WITHOUT any
-- tenant_id / principal_id / entitlement / authorization column (spec §2). No
-- hard FK to catalog on purpose ("FK-ish", spec §2): telemetry is observational
-- and must never fail to record just because a version isn't catalogued yet.
-- ---------------------------------------------------------------------------
create table if not exists lskills.telemetry (
  event_id uuid primary key default gen_random_uuid(),
  skill_id text not null,                              -- soft ref -> catalog.skill_id (no hard FK, see above)
  skill_version text,                                  -- which version actually ran
  agent_id text,                                       -- which agent/role invoked the skill
  program_ref text,                                    -- Program short-code label (lsites, lsales) -- NOT a tenant/authz key
  issue_ref text,                                      -- Program Ledger Issue id, if invoked inside one
  run_ref text,                                        -- Program Ledger Run id, if invoked inside one
  task_id text,                                        -- skill-local task id (YYYYMMDD-HHMM-<SKILL>-<UNIX>)
  status lskills.telemetry_status not null default 'initialized',
  outcome_detail jsonb not null default '{}'::jsonb,   -- error class, HITL reason, corrected-from, artifact refs
  duration_ms integer,                                 -- wall-clock duration
  cost jsonb,                                          -- {tokens_in, tokens_out, model, usd_estimate} -- observation only, no billing semantics
  summary text,                                        -- short human-readable summary
  created_at timestamptz not null default now()
);

comment on column lskills.telemetry.program_ref is
  'Program short-code LABEL only (e.g. lsites, lsales). Never a tenant or '
  'authorization key -- telemetry gates nothing (spec §2).';
comment on column lskills.telemetry.cost is
  'Cost OBSERVATION only ({tokens_in, tokens_out, model, usd_estimate}). '
  'Deliberately carries no billing/financial_ledger semantics -- that coupling '
  'was excised with the Logic Engine (ADR 0001).';

-- indexes -------------------------------------------------------------------
create index if not exists idx_lskills_catalog_state on lskills.catalog(certification_state);
create index if not exists idx_lskills_catalog_skill on lskills.catalog(skill_id);
create index if not exists idx_lskills_catalog_org on lskills.catalog(org_id);

create index if not exists idx_lskills_telemetry_skill on lskills.telemetry(skill_id, skill_version);
create index if not exists idx_lskills_telemetry_program on lskills.telemetry(program_ref);
create index if not exists idx_lskills_telemetry_status on lskills.telemetry(status);
create index if not exists idx_lskills_telemetry_created on lskills.telemetry(created_at);

create index if not exists idx_lskills_eval_runs_skill on lskills.eval_runs(skill_id, skill_version);
create index if not exists idx_lskills_eval_runs_passed on lskills.eval_runs(passed);
create index if not exists idx_lskills_eval_runs_created on lskills.eval_runs(created_at);

-- ---------------------------------------------------------------------------
-- HARD GATE: "usable requires a PASSING eval suite" (spec §1, §1.1).
--
-- The catalog CHECK constraints above already make it impossible for a `usable`
-- row to have a null/empty/placeholder eval_suite_ref. But the spec's real gate
-- is stronger and cross-table: a version may only be `usable` when the LATEST
-- eval_run for (skill_id, version) is a PASS. That can't be a CHECK (it reads
-- another table), so it is a BEFORE trigger on catalog. This is enforcement at
-- the data layer, not application-layer discipline.
-- ---------------------------------------------------------------------------
create or replace function lskills.enforce_usable_requires_passing_eval()
returns trigger
language plpgsql
as $$
declare
  latest_passed boolean;
begin
  if new.certification_state = 'usable' then
    select er.passed
      into latest_passed
      from lskills.eval_runs er
      where er.skill_id = new.skill_id
        and er.skill_version = new.version
      order by er.created_at desc
      limit 1;

    if latest_passed is null then
      raise exception
        'lskills.catalog: cannot set %/% to usable -- no eval_run exists for this version (an attached, PASSING eval suite is mandatory)',
        new.skill_id, new.version
        using errcode = 'check_violation';
    elsif not latest_passed then
      raise exception
        'lskills.catalog: cannot set %/% to usable -- the latest eval_run for this version did not pass',
        new.skill_id, new.version
        using errcode = 'check_violation';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_catalog_usable_requires_passing_eval on lskills.catalog;
create trigger trg_catalog_usable_requires_passing_eval
  before insert or update on lskills.catalog
  for each row execute function lskills.enforce_usable_requires_passing_eval();

-- ---------------------------------------------------------------------------
-- AUTO-DEMOTE on regression (spec §1.1: "usable -> (regression: new eval_run
-- fails threshold) -> eval_pending"). Keeps the "a usable version's latest run
-- passed" invariant true over time: when a failing run lands for a currently-
-- usable version, it is demoted back to eval_pending automatically. (Auto-
-- PROMOTION stays application-level -- the Librarian promotes only on a clean
-- improvement; the DB only enforces the gate and this safety demotion.)
-- ---------------------------------------------------------------------------
create or replace function lskills.demote_on_eval_regression()
returns trigger
language plpgsql
as $$
begin
  if not new.passed then
    update lskills.catalog
      set certification_state = 'eval_pending',
          updated_at = now()
      where skill_id = new.skill_id
        and version = new.skill_version
        and certification_state = 'usable';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_eval_runs_auto_demote on lskills.eval_runs;
create trigger trg_eval_runs_auto_demote
  after insert on lskills.eval_runs
  for each row execute function lskills.demote_on_eval_regression();

-- ---------------------------------------------------------------------------
-- Roles: least-privilege, matching the platform / lsites_ledger / lbrain
-- pattern. Two runtime roles plus a read-only observer:
--   * svc_lskills_runtime   -- agents: READ the catalog, WRITE telemetry.
--                              No write to catalog or eval_runs.
--   * svc_lskills_librarian -- the curation ("Librarian") process: writes
--                              eval_runs and advances catalog.certification_state.
--   * svc_observer          -- read-only, dashboards/audit (matches lsites/lbrain).
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

revoke all on schema lskills from public;
grant usage on schema lskills to svc_lskills_runtime, svc_lskills_librarian, svc_observer;

-- Agents: read the catalog, record telemetry. Deliberately NO write to catalog
-- (only the Librarian promotes) and NO write to eval_runs.
grant select on lskills.catalog to svc_lskills_runtime;
grant select, insert on lskills.telemetry to svc_lskills_runtime;
grant select on lskills.eval_runs to svc_lskills_runtime;

-- Librarian: full curation authority over catalog + eval_runs; reads telemetry
-- to prioritize improvement targets (spec §6).
grant select, insert, update on lskills.catalog to svc_lskills_librarian;
grant select, insert on lskills.eval_runs to svc_lskills_librarian;
grant select on lskills.telemetry to svc_lskills_librarian;

-- Observer: read-only everywhere.
grant select on all tables in schema lskills to svc_observer;

grant execute on function platform.has_org_access(uuid, platform.member_role)
  to svc_lskills_runtime, svc_lskills_librarian;

do $$
begin
  execute 'alter role svc_lskills_runtime set search_path = lskills, public';
  execute 'alter role svc_lskills_librarian set search_path = lskills, public';
end $$;

-- ---------------------------------------------------------------------------
-- RLS: enabled on every table. Skills data is GLOBAL/internal (see ORG-SCOPING
-- DECISION header), so policies are role-scoped rather than org-scoped for now.
-- Deferred hardening mirrors platform_foundation / lbrain: only least-privilege
-- svc_* roles touch these tables; an org-scoped SELECT policy on catalog.org_id
-- is added later if a per-org-licensed skill ever exists.
-- ---------------------------------------------------------------------------
alter table lskills.catalog enable row level security;
alter table lskills.telemetry enable row level security;
alter table lskills.eval_runs enable row level security;

-- catalog: agents read; the Librarian is the sole writer; observer reads.
drop policy if exists lskills_catalog_runtime_read on lskills.catalog;
create policy lskills_catalog_runtime_read on lskills.catalog
  for select to svc_lskills_runtime
  using (true);

drop policy if exists lskills_catalog_librarian_all on lskills.catalog;
create policy lskills_catalog_librarian_all on lskills.catalog
  for all to svc_lskills_librarian
  using (true) with check (true);

drop policy if exists lskills_catalog_observer_read on lskills.catalog;
create policy lskills_catalog_observer_read on lskills.catalog
  for select to svc_observer
  using (true);

-- telemetry: agents append their own invocation records + read; Librarian and
-- observer read. Observational -- no org gate (spec §2).
drop policy if exists lskills_telemetry_runtime_write on lskills.telemetry;
create policy lskills_telemetry_runtime_write on lskills.telemetry
  for all to svc_lskills_runtime
  using (true) with check (true);

drop policy if exists lskills_telemetry_librarian_read on lskills.telemetry;
create policy lskills_telemetry_librarian_read on lskills.telemetry
  for select to svc_lskills_librarian
  using (true);

drop policy if exists lskills_telemetry_observer_read on lskills.telemetry;
create policy lskills_telemetry_observer_read on lskills.telemetry
  for select to svc_observer
  using (true);

-- eval_runs: the Librarian writes; agents + observer read.
drop policy if exists lskills_eval_runs_librarian_all on lskills.eval_runs;
create policy lskills_eval_runs_librarian_all on lskills.eval_runs
  for all to svc_lskills_librarian
  using (true) with check (true);

drop policy if exists lskills_eval_runs_runtime_read on lskills.eval_runs;
create policy lskills_eval_runs_runtime_read on lskills.eval_runs
  for select to svc_lskills_runtime
  using (true);

drop policy if exists lskills_eval_runs_observer_read on lskills.eval_runs;
create policy lskills_eval_runs_observer_read on lskills.eval_runs
  for select to svc_observer
  using (true);

-- verification
select n.nspname as schema_name, count(*) as tables
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'lskills' and c.relkind = 'r'
group by n.nspname;

-- ---------------------------------------------------------------------------
-- DOWN-MIGRATION: intentionally NOT in this file.
-- ---------------------------------------------------------------------------
-- There is deliberately NO `-- migrate:down` / `drop schema ... cascade`
-- section here. An archived LiNKsites mirror-pattern migration once put a
-- `drop schema if exists ... cascade` in the SAME pasteable block as its
-- up-migration, which confused the Principal (a destructive drop sitting one
-- scroll below the create statements it was meant to reverse). Every migration
-- since has fixed this. To avoid a repeat: if a down-migration is ever needed,
-- it MUST live in its own clearly named, separately-dated file
-- (e.g. `20260715_000003_lskills_catalog_core_down.sql`) so a destructive
-- `drop schema lskills cascade` can never be pasted or applied by accident
-- alongside the create. This file only ever creates.
-- ---------------------------------------------------------------------------
