---
name: self-improvement
description: "The Librarian: on a schedule or telemetry-volume trigger, reads usage telemetry and eval-suite runs to propose and gate versioned upgrades to LiNKskills skills and tools."
usage_trigger: "Invoked asynchronously by the studio scheduler (periodic 'dreaming'/curation cadence) or when a telemetry-volume threshold is crossed — NOT by a human asking mid-session. Do not trigger this skill reactively inside another task."
version: 1.1.0
release_tag: v1.1.0
created: 2026-02-24
author: LiNKskills Library
tags: [meta, optimization, evolution, librarian]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not apply breaking changes without explicit migration path", "Do not change tools or skills without evidence from ledger/patterns/user request"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-24
---

# self-improvement (the Librarian)

## Invocation Model (Async / Periodic — NOT in-session)
This skill is the **Librarian**: the curation process that reads telemetry + eval runs and
proposes versioned upgrades. It is **not** invoked reactively by a human mid-session. It
runs on the studio scheduler's periodic "dreaming"/curation cadence (e.g. nightly) **or**
when a telemetry-volume threshold is crossed (e.g. ~250 new `execution_ledger.jsonl` rows
since the last run). The scheduling entrypoint is a CLI/worker the scheduler calls (see
`scripts/`); an agent must not launch it as a side effect of an unrelated task. If launched
in-session, fail-fast and report that the Librarian runs asynchronously.

## Decision Tree (Fail-Fast & Persistence)
0. Resume active improvement task from `.workdir/tasks/*/state.jsonl` if present.
1. Confirm the invocation is a scheduled/volume-triggered run (not a mid-session human request); otherwise stop and explain the async model.
2. Confirm evidence sources are available: `execution_ledger.jsonl` (usage telemetry: `program_ref`, `duration_ms`, `cost`, `outcome_detail`, `status`, `summary`), `references/old-patterns.md`, per-skill `references/eval-suite.yaml`, and any user-requested features.
3. Intelligence floor check (must run on the frontier tier: `high` / `gpt-5` — never a cheap/fast tier for this judgment step).
4. Tooling policy check (native cli, cli wrapper, direct api, mcp).
5. Classify specialist or generalist and use JIT (`get_tool_details`) if generalist.
6. Build evidence-backed improvement proposals only; each candidate version must be judged by an actual eval-suite re-run, not trend analysis alone.
7. Block proposals lacking measurable impact, a clean eval delta, or a rollback path.

## Rules

### Scope-In
- Aggregate failure/latency/HITL/cost trends from ledger telemetry (`program_ref`, `duration_ms`, `cost`, `outcome_detail`) to select **what** to improve.
- Cross-reference old-patterns and recent user feature requests.
- Re-run each candidate skill's `references/eval-suite.yaml` to decide **whether** the proposed version is actually better (rubric scores + `delta_vs_previous`).
- Produce versioned upgrade proposals for skills/tools with migration notes and eval evidence.
- Drive the `certification_state` curation gate: auto-advance clean improvements toward `usable`; leave ambiguous/regressed candidates `eval_pending` for Principal review; auto-demote a `usable` version whose fresh eval fails threshold to `eval_pending`.

### Scope-Out
- Do not propose speculative changes without evidence.
- Do not auto-promote on trend analysis alone — a candidate must clear its eval suite with a clean, no-regression delta.
- Do not remove safety or persistence primitives.
- Do not skip changelog and rollback guidance.
- Do not touch tenant governance, leases, entitlements, or permission-to-act (`certification_state` is a LiNKskills-internal curation gate only, not governance).

### Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: Use native cli to inspect ledger and references.
2. **Level 2 - CLI Wrapper Scripts**: Use cli wrapper scripts for deterministic analytics where available.
3. **Level 3 - Direct API**: Direct api only under exception conditions.
4. **Level 4 - MCP**: Use mcp for persistent session analytics only.

### Internal Persistence (Zero-Copy / Flat-File)
- Save phase snapshots to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save trend tables and proposal diffs as task-local flat files.
- Seek targeted fields for incremental analysis.

### Smart JIT Tool Loading (Mitigated)
- Activate JIT for generalist or >10 tools.
- Use `get_tool_details` and cache capability summaries before proposing cross-tool changes.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Load `execution_ledger.jsonl` (usage telemetry) and target old-patterns files; prioritize targets by real usage — most-invoked and highest-failure/highest-cost skills first — using `program_ref`, `duration_ms`, `cost`, and `outcome_detail`, not just `status`/`summary`.
2. Merge with explicit user-requested feature improvements.
3. Determine specialist/generalist profile and load JIT details if needed.
4. Validate input contract and checkpoint `INITIALIZED`.

### Phase 2: Trend Analysis (selects WHAT to improve)
5. Compute failure clusters, recurring blockers, HITL bottlenecks, and cost/latency outliers.
6. Map trends to candidate interventions (skill rule, schema tightening, tool upgrade) and draft the candidate version.
7. Checkpoint `IN_PROGRESS` with ranked opportunities.

### Phase 3: Eval-Suite Re-Run (decides WHETHER it is better)
8. For each candidate skill, locate `skills/<skill_id>/references/eval-suite.yaml`.
   - **If present:** run it against the candidate version. Apply deterministic `assertions` first, then a frontier-tier judge (`high`/`gpt-5`) scores each rubric dimension. Aggregate to `overall_score`; compute `delta_vs_previous` per dimension vs the current version.
   - **If absent:** do NOT silently skip. Record an explicit "no eval suite — cannot certify" gap for that skill and treat the candidate as non-auto-promotable (route to review / eval-suite authoring).
9. Checkpoint `IN_PROGRESS` with rubric scores, `overall_score`, `passed`, and `delta_vs_previous`.

### Phase 4: Promotion Decision & Gate (explicit criteria)
10. **Auto-promote toward `usable` only on a clean, no-regression improvement:** the candidate passes its suite (`overall_score >= pass_threshold`, no dimension below its `hard_fail_below`) **and** `delta_vs_previous` is equal-or-better on **every** rubric dimension **and** there is no size/complexity blowup (`size_metrics` — `skill_md_lines`, `total_skill_bytes`, `context_required` — not materially worse). **First-eval case (reconciled with the runner):** when there is no prior eval_run for the version, `delta_vs_previous` is `null` — there is no regression to measure against — so a *passing* first eval counts as clean and is promotable. This judgment call was implicit here; it is made explicit in `LiNKplatform/packages/librarian-runner` (`isCleanImprovement`).
11. **Otherwise escalate:** any regression on any dimension, any ambiguity/conflicting evidence, a size/complexity blowup, or a missing eval suite ⇒ leave the version `eval_pending` and checkpoint `PENDING_APPROVAL`, queuing a short pre-digested diff for Principal review. A currently-`usable` version whose fresh eval fails threshold is auto-demoted to `eval_pending`.

### Phase 5: Finalization, Self-Correction & Auditing
12. Emit prioritized improvement roadmap, per-candidate eval evidence, and the promote/escalate decision with rollback plan.
13. Validate output contract and checkpoint `COMPLETED`.
14. Append summary to `execution_ledger.jsonl` (telemetry — the natural write point for the Librarian's own run).
15. Save trace log and update old-patterns for analysis mistakes.

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `improvement_context` | `./references/schemas.json#/definitions/input` | Validate available evidence scope. |
| **Output** | `improvement_plan` | `./references/schemas.json#/definitions/output` | Validate versioned proposals with rollback info. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist analytical checkpoints. |

## Progressive Disclosure References
- Advanced trend analysis: `./advanced/advanced.md`
- Proposal rubric: `./references/api-specs.md`
- Historical anti-patterns: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
