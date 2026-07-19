-- migrate:up
-- LiNKskills catalog SEED -- a one-time backfill of the PRE-EXISTING skill
-- population into the new lskills.catalog table.
--
-- Context/authority:
--   * LiNKskills/docs/archive/specs/catalog-eval-telemetry-spec.md (§1 catalog columns,
--     §1.1 certification_state gate, §4 eval-suite path convention, §5 format
--     profiles, §7 phasing -- "backfill eval suites per-skill, behind the
--     certification_state != usable gate")
--   * LiNKskills/supabase/migrations/20260715_000002_lskills_catalog_core.sql
--     (the applied schema this seed populates: columns, CHECKs, and the
--     usable-requires-passing-eval trigger)
--
-- What this seed does and does NOT do:
--   * Inserts one row per skill folder currently under skills/ (34 skills),
--     using each skill's OWN SKILL.md frontmatter as the source of truth for
--     `version`, `display_name` (frontmatter name), `description`, and
--     `min_reasoning_tier` (frontmatter engine.min_reasoning_tier). Versions are
--     read from the skills themselves, not the flat manifest.json.
--   * Declares each skill's conventional eval_suite_ref path
--     (skills/<skill_id>/references/eval-suite.yaml). The NOT NULL + non-empty
--     CHECK on eval_suite_ref requires a DECLARED path for every row even before a
--     file exists at that path. As of this seed only four skills actually have a
--     real eval-suite.yaml on disk (market-analyst, persistent-qa, lead-engineer,
--     marketing-strategist -- authored alongside this migration); the rest declare
--     the path but the file is still TODO. That is intentional and correct per the
--     design: `certification_state` staying 'draft' is what signals "not yet
--     certified", NOT the presence/absence of the file (spec §1.1, §7).
--   * Sets certification_state = 'draft' for EVERY row. Nothing is marked 'usable':
--     that transition requires an actual PASSING lskills.eval_runs row (enforced by
--     the enforce_usable_requires_passing_eval trigger in 000002), and no eval_run
--     exists yet for any skill. Fabricating a fake passing eval_run just to flip a
--     row to 'usable' would defeat the entire certification gate, so it is NOT done.
--   * Sets org_id = NULL for every row (global/internal), per the ORG-SCOPING
--     DECISION recorded in 000002: skills are LiNKtrend's own internal library with
--     no per-tenant authorization semantics.
--
-- format_profile choice (explicit for every row, spec §5):
--   Only THREE skills currently DECLARE a `format_profile` in their SKILL.md
--   frontmatter -- citation-enforcer: simple, git-safeguard: simple,
--   skill-template: heavy. Every other skill omits the field, which the validator
--   and the catalog table both DEFAULT to 'heavy'. Rather than mixing "omit the
--   column" and "set it" across rows of a single INSERT, this seed sets
--   format_profile EXPLICITLY on every row for consistency and self-documentation:
--   'simple' for the two skills that declare simple, 'heavy' for all the rest
--   (which is exactly the value the table default would have applied anyway). No
--   profile is invented for any skill that does not declare one -- 'heavy' is the
--   documented default they already resolve to, not a new claim.
--
-- Re-runnable: uses `on conflict (skill_id, version) do nothing` so applying this
-- twice (or after some rows already exist) is a no-op for existing (skill_id,
-- version) pairs. PK is (skill_id, version) per 000002.
--
-- NOTE: like every migration this session, this file is WRITTEN + reviewed-ready
-- SQL only. It is NOT applied to any live database here; the Principal applies it
-- manually via the Supabase SQL Editor once the lskills schema exists.
--
-- (No `-- migrate:down` section: this is an additive INSERT seed guarded by
-- on-conflict; there is nothing destructive to reverse. If a down were ever wanted
-- it must live in its own clearly named file, per the 000002 convention.)

insert into lskills.catalog
  (skill_id, version, org_id, display_name, description, format_profile, eval_suite_ref, certification_state, min_reasoning_tier)
values
  ('audit-protocol', '1.0.0', null, 'audit-protocol', 'Enforces predictive auditing so intent is logged before any write-action across Google Workspace and n8n operations.', 'heavy', 'skills/audit-protocol/references/eval-suite.yaml', 'draft', 'balanced'),
  ('blocker-resolution', '1.0.0', null, 'blocker-resolution', 'Fail-fast escalation protocol for stuck worker agents that triggers Root Cause Analysis when PROGRESS.md remains Blocked for more than two turns.', 'heavy', 'skills/blocker-resolution/references/eval-suite.yaml', 'draft', 'high'),
  ('channel-ops', '1.0.0', null, 'channel-ops', 'Platform-specific channel operations skill for YouTube, TikTok, and X, covering scheduling, comment workflows, and support-to-sales conversion motions.', 'heavy', 'skills/channel-ops/references/eval-suite.yaml', 'draft', 'high'),
  ('citation-enforcer', '1.1.0', null, 'citation-enforcer', 'Enforces evidence-first reasoning by requiring source attribution for every material claim.', 'simple', 'skills/citation-enforcer/references/eval-suite.yaml', 'draft', 'high'),
  ('compliance-guardian', '1.0.0', null, 'compliance-guardian', 'Platform legal and terms specialist that monitors YouTube/Meta policy requirements, AI disclosure obligations, and safety standards before publication.', 'heavy', 'skills/compliance-guardian/references/eval-suite.yaml', 'draft', 'high'),
  ('creative-director', '1.0.0', null, 'creative-director', 'Senior Creative Lead persona that converts marketing briefs into structured asset orders and triggers rendering workflows through n8n-bridge.', 'heavy', 'skills/creative-director/references/eval-suite.yaml', 'draft', 'high'),
  ('creative-qa', '1.0.0', null, 'creative-qa', 'High-fidelity creative auditor that validates rendered assets against brand_guidelines.md and PRD, issuing mandatory PASS/FAIL with revision logic.', 'heavy', 'skills/creative-qa/references/eval-suite.yaml', 'draft', 'high'),
  ('department-head', '1.0.0', null, 'department-head', 'COO-level coordination skill for managing Lead Engineer and Persistent QA workstreams through PROGRESS.md-driven governance.', 'heavy', 'skills/department-head/references/eval-suite.yaml', 'draft', 'high'),
  ('devops-sre', '1.0.0', null, 'devops-sre', 'DevOps/SRE persona skill for automated Dockerization, VPS deployment hardening, and secure LSL_MASTER_KEY propagation.', 'heavy', 'skills/devops-sre/references/eval-suite.yaml', 'draft', 'high'),
  ('engagement-to-strategy-loop', '1.0.0', null, 'engagement-to-strategy-loop', 'Analyzes channel metrics (views, CTR, sentiment) and produces high-signal strategic feedback for marketing iteration loops.', 'heavy', 'skills/engagement-to-strategy-loop/references/eval-suite.yaml', 'draft', 'high'),
  ('executive-sync-8am', '1.0.0', null, 'executive-sync-8am', 'Executive sync orchestration skill that starts data collection at 06:00 Taipei, queries department leads, and consolidates Wins, Blockers, and Financial Health into the 08:00 AM briefing.', 'heavy', 'skills/executive-sync-8am/references/eval-suite.yaml', 'draft', 'high'),
  ('git-safeguard', '1.1.0', null, 'git-safeguard', 'Applies a mandatory safety checklist before git push operations to prevent accidental or unsafe repository publication.', 'simple', 'skills/git-safeguard/references/eval-suite.yaml', 'draft', 'balanced'),
  ('lead-engineer', '1.0.0', null, 'lead-engineer', 'Refactored senior execution model for PRD decomposition, factory.json routing, and sub-agent sessions_spawn coordination.', 'heavy', 'skills/lead-engineer/references/eval-suite.yaml', 'draft', 'high'),
  ('market-analyst', '1.0.0', null, 'market-analyst', 'Runs competitor teardown and SWOT analysis workflows using the research tool with confidence-based escalation and cost controls.', 'heavy', 'skills/market-analyst/references/eval-suite.yaml', 'draft', 'high'),
  ('marketing-strategist', '1.0.0', null, 'marketing-strategist', 'Senior VP of Growth persona that converts product PRDs into multi-channel growth strategies with SEO targets, ad spend projections, and funnel architecture.', 'heavy', 'skills/marketing-strategist/references/eval-suite.yaml', 'draft', 'high'),
  ('persistent-qa', '1.0.0', null, 'persistent-qa', 'Independent quality assurance skill that audits outputs and maintains recurring defect memory in Supabase-backed BUG_HISTORY.md artifacts.', 'heavy', 'skills/persistent-qa/references/eval-suite.yaml', 'draft', 'high'),
  ('prd-architect', '1.0.0', null, 'prd-architect', 'Converts a vibe or rough idea into a professional technical specification with scope, architecture, constraints, and delivery criteria.', 'heavy', 'skills/prd-architect/references/eval-suite.yaml', 'draft', 'high'),
  ('repository-manager', '1.0.0', null, 'repository-manager', 'Manages repository hygiene, progress sync handoffs, and safe Git flow enforcement for LiNKskills sessions.', 'heavy', 'skills/repository-manager/references/eval-suite.yaml', 'draft', 'balanced'),
  ('revenue-adapter-base', '1.0.0', null, 'revenue-adapter-base', 'Foundational revenue protocol that ingests heterogeneous monetization signals (YouTube, AdSense, Stripe) and normalizes them into Venture Studio Transaction records.', 'heavy', 'skills/revenue-adapter-base/references/eval-suite.yaml', 'draft', 'high'),
  ('search-strategy', '1.0.0', null, 'search-strategy', 'Defines research intent, tiered escalation, and HITL controls for cost-aware evidence retrieval workflows.', 'heavy', 'skills/search-strategy/references/eval-suite.yaml', 'draft', 'high'),
  ('self-critique-loop', '1.0.0', null, 'self-critique-loop', 'Runs a System 2 audit loop that stress-tests draft outputs for correctness, consistency, and risk before release.', 'heavy', 'skills/self-critique-loop/references/eval-suite.yaml', 'draft', 'high'),
  ('self-improvement', '1.1.0', null, 'self-improvement', 'The Librarian: on a schedule or telemetry-volume trigger, reads usage telemetry and eval-suite runs to propose and gate versioned upgrades to LiNKskills skills and tools.', 'heavy', 'skills/self-improvement/references/eval-suite.yaml', 'draft', 'high'),
  ('seo-semantic-auditor', '1.0.0', null, 'seo-semantic-auditor', 'Reverse-engineers competitor keyword strategies using research tiers (Brave/Exa) and outputs prioritized content gaps for content operations.', 'heavy', 'skills/seo-semantic-auditor/references/eval-suite.yaml', 'draft', 'high'),
  ('skill-architect', '1.5.0', null, 'skill-architect', 'Designs, migrates, and refines production-grade skills following the LiNKskills Golden Template.', 'heavy', 'skills/skill-architect/references/eval-suite.yaml', 'draft', 'high'),
  ('skill-template', '1.2.0', null, 'skill-template', 'Golden template for creating production-grade LiNKskills skills.', 'heavy', 'skills/skill-template/references/eval-suite.yaml', 'draft', 'balanced'),
  ('smart-file-clerk', '1.0.0', null, 'smart-file-clerk', 'Senior Document Manager skill for hybrid storage orchestration: Supabase Buckets for active RAG and Google Drive for deep archive, with OCR pipelines for financial/legal documents.', 'heavy', 'skills/smart-file-clerk/references/eval-suite.yaml', 'draft', 'high'),
  ('software-pm', '1.0.0', null, 'software-pm', 'Software project management orchestrator that converts PRDs into technical backlogs aligned to SaaS/Web factories and enforces QA-backed Definition of Done.', 'heavy', 'skills/software-pm/references/eval-suite.yaml', 'draft', 'high'),
  ('studio-architect', '1.0.0', null, 'studio-architect', 'Template-first architecture skill that enforces factory.json discovery and initialization from approved starter kits before custom development.', 'heavy', 'skills/studio-architect/references/eval-suite.yaml', 'draft', 'high'),
  ('studio-controller', '1.0.0', null, 'studio-controller', 'Financial oversight skill implementing GAAP reporting (P&L, Balance Sheet, Cashflow, AR/AP, Budget vs Actual) with Supabase lsl_finance logging and reconciliation controls.', 'heavy', 'skills/studio-controller/references/eval-suite.yaml', 'draft', 'high'),
  ('studio-health-reporting', '1.0.0', null, 'studio-health-reporting', 'Aggregates lsl_memory.audit_logs and PROGRESS.md streams into a Venture Studio Health Report for COO oversight.', 'heavy', 'skills/studio-health-reporting/references/eval-suite.yaml', 'draft', 'high'),
  ('task-decomposition', '1.0.0', null, 'task-decomposition', 'Applies Factored Cognition to decompose complex studio work into atomic, verifiable execution steps.', 'heavy', 'skills/task-decomposition/references/eval-suite.yaml', 'draft', 'high'),
  ('tool-architect', '1.0.0', null, 'tool-architect', 'Designs, wraps, and validates CLI-first tools for the LiNKskills Global Tools Registry.', 'heavy', 'skills/tool-architect/references/eval-suite.yaml', 'draft', 'balanced'),
  ('ui-ux-guardian', '1.0.0', null, 'ui-ux-guardian', 'Design system guardian skill for enforcing Studio CSS standards and Playwright-based visual regression controls.', 'heavy', 'skills/ui-ux-guardian/references/eval-suite.yaml', 'draft', 'high'),
  ('workflow-architect', '1.0.0', null, 'workflow-architect', 'Designs, creates, activates, and validates n8n workflows from structured task requirements.', 'heavy', 'skills/workflow-architect/references/eval-suite.yaml', 'draft', 'balanced')
on conflict (skill_id, version) do nothing;

-- verification: how many skill versions are now catalogued.
select count(*) from lskills.catalog;
