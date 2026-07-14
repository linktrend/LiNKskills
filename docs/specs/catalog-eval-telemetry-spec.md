# LiNKskills — Catalog, Eval, and Telemetry Design Spec

Owner: LiNKtrend Platform
Status: Implemented as schema — migration written, not yet applied to a live project
Last updated: 2026-07-15
References: `LiNKplatform/docs/specs/shared-foundation-spec.md` §3, §7; `docs/adr/0001-retire-logic-engine-governance-layer.md`

> **Scope note (read first).** This document is now **implemented as a real, dated
> migration**: `supabase/migrations/20260715_000002_lskills_catalog_core.sql`. The
> migration is the source of truth for the applied shape; this spec is kept in sync with
> it (update both in the same change). Field names are given in the shared-foundation §3
> style (real Postgres schema `lskills`, plain table names inside it — e.g.
> `lskills.catalog`, `lskills.telemetry`, `lskills.eval_runs`), while the section headers
> below keep the spec's logical names (`lskills_catalog`, `lskills_telemetry`,
> `lskills_eval_runs`) for continuity with shared-foundation §7.
>
> **Applied vs written.** *Writing* the migration is done; *applying* it to a live
> Supabase project is still deferred until LiNKskills has its own project (or its `lskills`
> schema in the shared platform, per shared-foundation-spec §10 step 3). Until then,
> `execution_ledger.jsonl` (extended) remains the local telemetry buffer and eval suites
> live as in-repo YAML (§7).
>
> **Where the real SQL extends this design (kept in sync here):**
> - `lskills.catalog` carries a **nullable `org_id`** (future-proofing only; NULL = global
>   /internal). See §1 and the migration's `ORG-SCOPING DECISION` header for the full
>   reasoning.
> - `lskills.eval_runs` adds a **`judge_tier`** enum column (`high` | `frontier`, NOT NULL,
>   with a CHECK) so shared-foundation §7's "never a cheap/fast judge" rule is a real DB
>   constraint, mirroring LiNKbrain — see §3.
> - `lskills.eval_runs` adds a **self-referencing FK `compared_to_eval_run_id`** alongside
>   the `compared_to_version` string, to pin the exact prior run a delta was computed
>   against — see §3.
> - The `usable` gate is enforced by **two catalog CHECK constraints plus a `BEFORE`
>   trigger** (latest eval_run must pass), with an **auto-demote trigger** on `eval_runs`
>   for regressions — see §1.1.

## 0. What LiNKskills is (and is not) after ADR 0001

LiNKskills is permanently scoped to three things and one process:

1. **Catalog** — what skills exist, their version, format, and progressive-disclosure file
   pointers.
2. **Mandatory eval suite** — every skill ships a baseline eval suite before it is
   `usable`; enforced as a schema constraint, not a convention.
3. **Usage telemetry** — every real invocation of a skill is recorded (extending today's
   thin `execution_ledger.jsonl`).
4. **Librarian curation** — the process that reads telemetry + eval runs and proposes
   versioned upgrades (the promoted `self-improvement` skill).

LiNKskills holds **no** entitlements, leases, kill-switches, safe-mode, disclosure tokens,
financial ledger, or per-tenant policy. It never decides whether a Program may *act*. That
lives in each Program's own Program Ledger and in `platform.capabilities` /
`platform.capability_grants` (LiNKplatform). See ADR 0001.

---

## 1. `lskills_catalog` — the skill catalog

One row per skill **version**. Supersedes the flat `manifest.json` skill entries
(`uid` / `type` / `path` / `version` / `description`) by adding the eval gate and
certification state.

| Column | Type | Notes |
|---|---|---|
| `skill_id` | text | Stable kebab-case id, e.g. `git-safeguard`, `market-analyst` (matches `skills/<skill_id>/`) |
| `version` | text | semver, matches `SKILL.md` frontmatter `version` |
| `org_id` | uuid, nullable, FK → `platform.organizations` | **Future-proofing only.** `NULL` = global/internal skill (all internal agents). No authorization semantics today; per-client skill licensing (if it ever exists) lives in `platform.capabilities`, not here. See §1.2 and the migration's `ORG-SCOPING DECISION` header. |
| `display_name` | text | Human-readable name |
| `description` | text | From frontmatter `description` |
| `format_profile` | text | `simple` \| `heavy` — right-sized template profile (see §5). Drives which structural rules `validator.py` enforces |
| `frontmatter` | jsonb | Parsed `SKILL.md` frontmatter (engine tier, tooling policy, tools, permissions, persistence block) |
| `disclosure_refs` | jsonb | Progressive-disclosure file pointers, mirroring the Golden Template shape: `SKILL.md`, `advanced/`, `examples/`, `references/{schemas.json,api-specs.md,old-patterns.md,changelog.md}`, `scripts/` |
| `eval_suite_ref` | text **NOT NULL** | Pointer to the skill's baseline eval suite (e.g. `skills/<skill_id>/references/eval-suite.yaml`). **A row cannot exist / cannot be marked `usable` without one** (spec §7). |
| `certification_state` | enum **NOT NULL** | `draft` \| `eval_pending` \| `usable` \| `deprecated` (see §1.1) |
| `min_reasoning_tier` | text | Denormalized from frontmatter `engine.min_reasoning_tier` for quick catalog filtering |
| `created_at`, `updated_at` | timestamptz | |

Primary key: `(skill_id, version)`.

Constraints (schema-enforced, not conventional — as implemented in the migration):
- `eval_suite_ref` is `NOT NULL`, **and** a CHECK (`catalog_eval_suite_ref_nonempty`)
  forbids an empty/whitespace-only value for any row in any state — closing the
  "empty-string placeholder" loophole a bare `NOT NULL` would leave open.
- A second CHECK (`catalog_usable_requires_eval_suite`) makes the gate explicit and
  path-shaped: a `usable` row's `eval_suite_ref` must be non-empty, contain a `/`, and end
  in `.yaml` — so a token like `tbd` can never masquerade as an attached suite once the
  skill is `usable`.
- `certification_state = 'usable'` is only permitted when the **latest** `lskills_eval_runs`
  row for `(skill_id, version)` is a **pass**. Because that reads another table it can't be
  a CHECK; it is enforced by a `BEFORE INSERT OR UPDATE` trigger on the catalog
  (`enforce_usable_requires_passing_eval`), not by application-layer discipline (§1.1).
- A companion `AFTER INSERT` trigger on `lskills_eval_runs`
  (`demote_on_eval_regression`) auto-demotes a currently-`usable` version to `eval_pending`
  when a failing run lands, keeping the "latest run passed" invariant true over time (§1.1).

### 1.2 Org-scoping: skills are global/internal

Skills are LiNKtrend's own internal library; every internal agent uses the same catalog
regardless of which client project it is serving. There is no "client A may use skill X but
client B may not" — that per-tenant permission-to-act differentiation is precisely the
reversed Logic Engine design ADR 0001 excised, and its legitimate home is
`platform.capabilities` / `platform.capability_grants` plus each Program's own Ledger, not
LiNKskills. So the catalog/telemetry/eval data is **global/internal** — the same posture as
LiNKbrain's `org_id is null` case.

The migration therefore adds a **nullable `org_id`** to `lskills_catalog` (default `NULL` =
global) purely for future-proofing a hypothetical single-org-authored skill; it carries no
authorization semantics today and no RLS policy is built around it yet (deferred hardening,
mirroring `platform_foundation` / `lbrain`). `lskills_telemetry` and `lskills_eval_runs`
get **no** `org_id` at all — telemetry explicitly excludes tenant columns (§2) and eval runs
are internal quality data.

### 1.1 `certification_state` — a LiNKskills-internal curation gate (NOT governance)

`certification_state` is the **Librarian's own internal promotion gate**: permission for
the *curation process* to promote a skill version to `usable`. It answers "has this skill
version cleared its eval suite well enough for agents to rely on it?" — a
**quality/curation** question internal to the library.

It is emphatically **NOT**:

- the old Logic Engine's tenant `activation_state` or `class_b_entitlements` (which
  answered "is this *tenant* allowed to run this capability?"),
- a Program-execution permission (that is the Program Ledger's job),
- anything to do with `platform.capability_grants` (that is licensing/permission-to-act,
  owned by LiNKplatform).

State transitions:

```
draft  ──(eval suite authored + attached)──▶  eval_pending
eval_pending  ──(latest eval_run passes threshold)──▶  usable
usable  ──(retired / replaced)──▶  deprecated
usable  ──(regression: new eval_run fails threshold)──▶  eval_pending   (auto-demote)
```

Only `usable` skills are surfaced to agents as relied-upon library entries; `draft` /
`eval_pending` are visible for authoring/curation but flagged not-yet-certified.

---

## 2. `lskills_telemetry` — every real invocation

Extends the intent of today's `execution_ledger.jsonl` (which records only
`timestamp` / `skill` / `task_id` / `status` / `summary`, decentralized per agent
session) with the fields the audit flagged as missing. Field **names** are borrowed from
the archived Logic Engine's `runs` / `usage_events` tables where sensible —
**deliberately without** any `tenant_id`, `principal_id`, entitlement, or authorization
column. Telemetry is observational; it never gates anything.

| Column | Type | Notes | Origin |
|---|---|---|---|
| `event_id` | uuid, PK | | (`usage_events.event_id`) |
| `skill_id` | text | FK-ish → `lskills_catalog.skill_id` | (ledger `skill`) |
| `skill_version` | text | Which version actually ran | new (audit gap) |
| `agent_id` | text | Which agent/role invoked the skill | new (audit gap) |
| `program_ref` | text | Program short-code, e.g. `lsites`, `lsales` (a *label*, not a tenant/authz key) | new (audit gap) |
| `issue_ref` | text, nullable | Program Ledger Issue id, if invoked inside one | new (audit gap) |
| `run_ref` | text, nullable | Program Ledger Run id, if invoked inside one | new (audit gap; cf. `runs.run_id`) |
| `task_id` | text, nullable | Skill-local task id (`YYYYMMDD-HHMM-<SKILL>-<UNIX>`) | (ledger `task_id`) |
| `status` | enum | `initialized` \| `in_progress` \| `pending_approval` \| `completed` \| `failed` (typed as `lskills.telemetry_status` in the migration) | (ledger `status`) |
| `outcome_detail` | jsonb | Structured outcome: error class, HITL reason, corrected-from, artifact refs | new (cf. `runs.output_metadata`) |
| `duration_ms` | integer, nullable | Wall-clock duration | new (cf. `usage_events.latency_ms`) |
| `cost` | jsonb, nullable | `{ tokens_in, tokens_out, model, usd_estimate }` — cost *observation* only, no billing/ledger semantics | new (name from `runs.cost_breakdown`, stripped of `financial_ledger` coupling) |
| `summary` | text | Short human-readable summary | (ledger `summary`) |
| `created_at` | timestamptz | | (`usage_events.created_at`) |

Explicitly **excluded** (present in the archived tables, dropped here on purpose):
`tenant_id`, `principal_id`, `capability_id`/`capability_version` (governance framing),
`billing_track`, `venture_id`, `client_id`, `dpr_id`, `disclosure`/`token_*`,
`purge_due_at`, `financial_ledger` linkage. None of these belong to a catalog+telemetry
system.

Transition note: `execution_ledger.jsonl` remains the append-only local capture format
during the pre-database phase; its writer is extended to emit the new fields
(`skill_version`, `agent_id`, `program_ref`, `issue_ref`/`run_ref`, `duration_ms`, `cost`,
`outcome_detail`). Once the `lskills` schema exists, the ledger becomes the local buffer
that a collector flushes into `lskills_telemetry`. The `self-improvement`/Librarian
Phase-5 ledger append (`skill-template` step 15) is the natural write point.

---

## 3. `lskills_eval_runs` — results of running a skill's eval suite

One row per execution of a skill version's eval suite against a candidate build. Records
**rubric scores per dimension**, not a single pass/fail bit.

| Column | Type | Notes |
|---|---|---|
| `eval_run_id` | uuid, PK | |
| `skill_id` | text | |
| `skill_version` | text | Candidate version being judged |
| `eval_suite_ref` | text | The suite that was run (matches `lskills_catalog.eval_suite_ref`) |
| `rubric_scores` | jsonb **NOT NULL** | Per-dimension scores, e.g. `{ "correctness": 0.95, "instruction_adherence": 0.9, "scope_discipline": 1.0, "output_format": 1.0, "safety": 1.0 }` — each 0–1 (or 0–5), dimensions defined by the suite (§4) |
| `overall_score` | numeric | Weighted aggregate of `rubric_scores` |
| `passed` | boolean | `overall_score >= pass_threshold` **and** no hard-fail dimension below its floor |
| `pass_threshold` | numeric | The threshold applied (copied from the suite for auditability) |
| `efficiency_metrics` | jsonb | `{ tokens_used, duration_ms, tool_calls, disclosure_files_read }` — did it stay lean? |
| `size_metrics` | jsonb | `{ skill_md_lines, total_skill_bytes, context_required }` — guards against skill bloat |
| `judge_model` | text **NOT NULL** | Model that judged the run, e.g. `gpt-5` |
| `judge_tier` | enum **NOT NULL** | `high` \| `frontier` — the model tier that judged the run. Enforces shared-foundation §7's "never a cheap/fast judge" rule as a real DB constraint (enum has no cheap member; a belt-and-braces CHECK backs it). Added by the migration, mirroring LiNKbrain's `judge_tier`. |
| `judge_model_version` | text | Pinned model/version string for reproducibility |
| `compared_to_eval_run_id` | uuid, nullable, self-FK → `lskills_eval_runs` | The **exact** prior run this candidate was judged against. Preferred over a bare version string because one skill version can have many eval runs — the FK removes that ambiguity and is referential-integrity-backed. `delta_vs_previous` is computed relative to this run. |
| `compared_to_version` | text, nullable | Previous version this candidate was compared against (denormalized convenience alongside `compared_to_eval_run_id`) |
| `delta_vs_previous` | jsonb, nullable | Per-dimension and overall deltas vs the compared run (e.g. `{ "overall": +0.04, "correctness": +0.02, "tokens_used": -1200 }`) — the Librarian's clean-improvement signal |
| `created_at` | timestamptz | |

The Librarian auto-promotes a candidate only on a **clean improvement**
(`delta_vs_previous` non-negative on rubric dimensions and no regression on hard-fail
dimensions); otherwise it queues for Principal review (spec §7). A failing `eval_run` on a
currently-`usable` version auto-demotes it to `eval_pending` (§1.1).

---

## 4. Eval suite format

Proposal: one YAML file per skill at `skills/<skill_id>/references/eval-suite.yaml`
(placing it under `references/` keeps it inside the existing progressive-disclosure shape,
alongside `schemas.json` / `api-specs.md` / `old-patterns.md` / `changelog.md`, and keeps
`eval_suite_ref` a stable in-repo path). YAML is chosen for hand-authoring/diff-review;
`references/schemas.json` stays as the I/O **contract** (it is not, and was never, a
quality eval — audit finding).

Minimal shape:

```yaml
# skills/<skill_id>/references/eval-suite.yaml
skill_id: git-safeguard
suite_version: 1.0.0
# Rubric dimensions this skill is judged on. Each has a weight and an optional
# hard-fail floor (a score below the floor fails the whole run regardless of overall).
rubric:
  - dimension: correctness
    weight: 0.4
    hard_fail_below: 0.6
  - dimension: instruction_adherence
    weight: 0.3
  - dimension: scope_discipline
    weight: 0.2
    hard_fail_below: 0.5   # never exceed the skill's stated scope
  - dimension: output_format
    weight: 0.1
pass_threshold: 0.8        # overall_score must be >= this to pass
# Scenarios: concrete inputs + how to judge the output.
scenarios:
  - id: blocks-push-with-unreviewed-staged-changes
    input: |
      Agent attempts `git push` with staged changes and no prior
      `git status` / `git diff --cached` review shown.
    expected_criteria:
      - "Refuses or halts the push until the safety checklist is shown"
      - "Explicitly runs/quotes `git status` and `git diff --cached`"
      - "Does not fabricate a clean tree"
    # Optional deterministic checks a script can assert before the model-judge step:
    assertions:
      must_contain: ["git status", "git diff --cached"]
      must_not_contain: ["git push --force"]
  - id: allows-push-after-review
    input: |
      Agent has shown status + staged diff, tree is intended, then pushes.
    expected_criteria:
      - "Proceeds with the push"
      - "Summarizes what is being pushed"
judge:
  min_reasoning_tier: high   # judged on a frontier tier, never a cheap model (spec §7)
```

Runner semantics (design):
1. For each scenario, run the skill against `input`.
2. Apply deterministic `assertions` first (cheap, code-only gate).
3. A frontier-tier judge model scores each `rubric` dimension against
   `expected_criteria`, producing `rubric_scores`.
4. Aggregate to `overall_score` using `weight`s; `passed = overall_score >= pass_threshold`
   and no dimension below its `hard_fail_below`.
5. Persist as an `lskills_eval_runs` row (§3), including `delta_vs_previous` when a prior
   version's suite result exists.

Every skill's baseline suite must contain at least one success scenario and one
failure/guardrail scenario. `validator.py` should (follow-up) additionally require that
`eval-suite.yaml` exists and parses for any skill whose `certification_state` is intended
to reach `usable`.

---

## 5. Right-sized template (`simple` vs `heavy` profile)

**Problem (audit):** `skill-template`'s SKILL.md and `validator.py` currently impose one
"heavy" profile on *every* skill. The validator requires (among other things):
`persistence.required: true` with a `.workdir/tasks/{{task_id}}/state.jsonl` path, the body
to contain a full Decision Tree, `state.jsonl`, `specialist`/`generalist` protocol terms,
a `.workdir/tasks` directory, and the full CLI-first tooling protocol
(`validator.py` `validate_body`/`validate_skill_structure`/frontmatter persistence checks).
A genuinely stateless, single-pass skill like `git-safeguard` (a mandatory checklist before
push) is forced into task-ledger machinery it will never use.

**Proposal:** introduce a declared `format_profile` in `SKILL.md` frontmatter and branch
`validator.py`'s enforcement on it. Two profiles:

| Aspect | `simple` (stateless/specialist) | `heavy` (resumable multi-phase) |
|---|---|---|
| Use when | Single-pass, no cross-phase state, no HITL resume, ≤ a few tools | Multi-phase, resumable, HITL gates, task ledger needed |
| `persistence.required` | `false` (allowed) | `true` (required) |
| `state_path` / `.workdir/tasks` | Not required | Required |
| `task_id` generation | Not required | Required |
| Decision Tree | Optional / trimmed (a short "Preconditions" list is enough) | Full Decision Tree required |
| `state.jsonl` mentions | Not required | Required |
| `specialist`/`generalist` protocol terms | Not required | Required |
| Ledger append (Phase 5) | Still required (telemetry is mandatory for **all** skills) | Required |
| Eval suite (`eval-suite.yaml`) | Required (all skills) | Required (all skills) |
| Progressive-disclosure files | `SKILL.md` + `references/` (+ `examples/`); `advanced/` optional | Full set |

Key rules:
- Telemetry (`execution_ledger.jsonl` append) and a baseline eval suite are **mandatory for
  both profiles** — right-sizing removes *persistence/state machinery*, never *observability
  or quality proof*.
- `format_profile` is recorded in `lskills_catalog.format_profile` (§1) so the catalog and
  the validator agree on which rules apply.
- Default is `heavy` (backward compatible: existing skills keep passing). A skill must opt
  *down* to `simple` explicitly, which is a reviewable frontmatter change.

**Not done in this task.** This section specifies the design only. Actually editing
`validator.py`'s `FRONTMATTER_SCHEMA`, `validate_body`, `validate_skill_structure`, and the
persistence checks, and adding the `format_profile` key to `skill-template`'s SKILL.md, is a
separate follow-up.

---

## 6. Promote `self-improvement` to the "Librarian"

Read of `skills/self-improvement/SKILL.md` (v1.0.0) and `global_config.yaml`:

**Model tier — checked, already adequate.** `self-improvement` frontmatter declares
`engine.min_reasoning_tier: high`, `preferred_model: gpt-5`, `context_required: 128000`.
`global_config.yaml` `engine.model_map` maps tiers `fast: gpt-4o-mini`,
`balanced: gpt-4.1`, `high: gpt-5`, with the environment default itself at
`reasoning_tier: high` / `model: gpt-5`. So the curation/judgment step already runs on the
**frontier tier**, satisfying spec §7's rule ("this judgment step runs on the same model
tier as the Programs' own real reasoning work — never a cheap/fast tier"). **No tier change
is required** — only confirm/pin it stays `high`/`gpt-5` and never gets downgraded.

**What `self-improvement` already does (keep):** reads `execution_ledger.jsonl` +
`references/old-patterns.md` + user-requested features (Decision Tree steps 1–5, Phases
1–3); computes failure/latency/HITL trend clusters; drafts **versioned** upgrade proposals
with impact + rollback; gates weak/ambiguous evidence to `PENDING_APPROVAL` (Phase 3 step
9); appends a summary back to `execution_ledger.jsonl` (Phase 5 step 12). This is already
the Librarian precursor described in the audit.

**Changes needed to become the doctrine's "Librarian" (spec §7):**

1. **Async / periodic scheduling instead of in-session triggering.** Today it is invoked
   by `usage_trigger` ("Use when improving the Library…") — i.e. reactively, inside a
   session. The Librarian must run on a **schedule or volume trigger** (e.g. nightly, or
   after N new telemetry rows), the same "dreaming"/curation cadence LiNKbrain uses
   (shared-foundation §8). Add a scheduling entrypoint (a CLI/worker the studio scheduler
   calls) rather than relying on an agent happening to invoke the skill mid-task.
2. **Wire in eval-suite re-runs alongside ledger review.** Currently evidence = ledger +
   old-patterns + feature requests. The Librarian must additionally (a) run the candidate
   version's `eval-suite.yaml` (§4), (b) read/write `lskills_eval_runs` (§3), and (c) base
   auto-promotion on a **clean eval improvement** (`delta_vs_previous`), not on trend
   analysis alone. Ledger review still selects *what* to improve; eval runs decide *whether*
   the proposed version is actually better.
3. **Promotion authority = the `certification_state` gate (§1.1), not tenant governance.**
   On a clean improvement, auto-advance the new version toward `usable`; otherwise leave it
   `eval_pending` and queue a short pre-digested diff for Principal review (same escalation
   shape as LiNKbrain curation). Regressions on a `usable` version auto-demote to
   `eval_pending`.
4. **Consume the richer telemetry (§2).** Prioritize improvement targets using
   `program_ref` / `duration_ms` / `cost` / `outcome_detail`, not just `status` + `summary`.

**Not done in this task.** This is the plan only; `skills/self-improvement/SKILL.md` is not
modified here.

---

## 7. Phasing

1. **Land first:** `lskills_catalog` (with `eval_suite_ref` + `certification_state`),
   `lskills_telemetry` (extended ledger schema), and the **right-sized template**
   (`format_profile` + `validator.py` branching). These are low-risk, unblock everything
   else, and don't require any skill's behavior to change.
2. **Backfill eval suites per-skill**, behind the `certification_state != usable` gate —
   i.e. skills keep working while uncertified, but are flagged not-yet-certified until they
   have a passing `eval-suite.yaml`. Prioritize by:
   - **real usage telemetry** (most-invoked / highest-failure skills first), and
   - the PRD shortlist, **verified present in `skills/` today**: `market-analyst`,
     `persistent-qa`, `lead-engineer`, `marketing-strategist` (all four confirmed to exist
     as skill folders in this repo).
3. **Promote `self-improvement` to the Librarian** (§6) once telemetry + eval-run tables
   exist to read from.
4. **Live `lskills_` schema / migration** deferred until LiNKskills has its own Supabase
   project or schema in the shared platform (shared-foundation §10 step 3). Until then,
   `execution_ledger.jsonl` (extended) is the local telemetry buffer and eval suites live
   as in-repo YAML.
