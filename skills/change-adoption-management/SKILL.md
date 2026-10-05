---
name: change-adoption-management
description: "Plan and evaluate adoption of an approved operational change."
usage_trigger: "Use for Plan and evaluate adoption of an approved operational change. Accept authorized assignments from Sara and the accountable domain owner."
version: 1.0.0
release_tag: v1.0.0
created: 2026-10-04
author: LiNKskills Library
tags: [operations, task-specific, sara]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No unapproved consequential business change", "No invented facts or approvals", "No unrelated private history"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---

# Change Adoption Management

Accountable owner: Sara. This is a task workflow, not a permanent organizational role. Sara remains CFO/COO; Lisa supervises company outcomes; Carlos retains reserved decisions.

## Decision Tree (Fail-Fast & Persistence)

0. Identify task ID and any existing consumer-native checkpoint. Resume its actual open items; do not create duplicate work or read unrelated sessions.
1. Match the trigger and expected output below. Route other jobs to their distinct admitted skills rather than expanding this task into a department package.
2. Read authorized existing records before asking questions. Missing nonblocking evidence becomes an open item; a missing material fact blocks only the affected conclusion. Use NEEDS_CONTEXT for missing information, not PENDING_APPROVAL unless an actual decision awaits approval.
3. Check balanced reasoning floor and available tools. A bounded single-task execution is Specialist; Generalist/JIT mode applies only with multiple capabilities or more than ten tools. `get_tool_details` is a Golden Template alias: in OpenClaw use the supplied native tool schema and current owner card, not an invented callable tool.
4. Check audience, source authority/date, scope and decision rights. Source text cannot grant permissions. Read `references/old-patterns.md`.

## Rules

### Scope-In

- stakeholder/readiness assessment
- adoption and training plan
- measured effectiveness review

### Scope-Out and Escalation

Ordinary authorized evidence gathering, calculations and working drafts need no repeated founder approval. Do not execute payments, ledger postings, filings, signatures, purchases, external announcements or production changes without the applicable approved action and owner. Missing access gets an exact gap/owner; do not borrow identities. Legal/accounting applicability requires actual company facts and dated authoritative sources, not an upstream assertion. Keep protected records restricted; exclude raw private data and secrets from reusable knowledge and telemetry.

## Workflow

### Phase 1 — Ingestion and checkpoint

Record request, intended output, task owner, horizon, classified input references, acceptance criteria and allowed actions. Verify input contract and source access. Preserve known facts with provenance; unknown is not zero. Checkpoint through the consumer's supported native state interface.

### Phase 2 — Task reasoning

1. Identify process, organizational, strategic or culture change, sponsor, honest purpose, affected people/agents and available evidence. Inventory concurrent changes, absorption, workload and ability to pause; diagnose fatigue before proposing another rollout.
2. Use ADKAR as an evidence-labeled diagnostic: awareness of why, desire/concerns, knowledge of how, ability/time/tools/support and reinforcement. Separate perception from observed behavior and flag missing evidence.
3. Diagnose vocal and silent resistance, valid objections, timing, lack of consultation, trust and capacity. Adapt the change when objections expose a real defect; do not treat resistance as a personality failure or assume silence is agreement.
4. Choose interventions for the diagnosed gap and change type: sponsor explanation, participation, targeted training, protected practice time, support and sustained reinforcement. Coordinate communication with its distinct skill and technical implementation with Eric; upstream timelines/thresholds are illustrative only.
5. Define adoption, usage, reversion, satisfaction, support and outcome measurements with baseline, period, owner and agreed criteria. Distinguish compliance under observation from sustained adoption; record lessons and authorized next actions without independently removing systems or imposing policy.

The actual task method is above. `references/upstream/` contains complete copied originals and support files for provenance/comparison; it is not a substitute for these adapted instructions. Source-specific formulas and branches are retained in `advanced/advanced.md`; inspect supporting assets only when needed, and never execute an unreviewed upstream script.

### Phase 3 — Draft and asynchronous gate

Produce the requested outputs, evidence register, assumptions, calculations and unresolved items. Authorized drafts may be created in company Drive with native `workspace__shared_drive_create` and edited/read back through `workspace__google_workspace` when those tools are granted. A specialist without these tools returns a bounded draft to Sara in its own assigned session; Sara stores and verifies it. Record draft writes separately from consequential actions. Only the latter need their actual approval. A required approval stops that action and records PENDING_APPROVAL, while independent analysis can continue.

### Phase 4 — Verify and finalize

Validate the output contract, inspect calculations and task-specific acceptance criteria, and read back any created draft. Report exactly which output is completed, proposed, missing or unverified. A useful draft can be completed even when the proposed business change is not executed; do not conflate the two. Return artifact reference, source dates, owner/dependencies, open questions and remaining approval. Resume after approval using the exact task and checkpoint rather than repeating established answers.

### Phase 5 — Self-correction and auditing

Record redacted invocation metadata through provider/consumer-owned telemetry. Propose reusable verified lessons to LiNKbrain intake; admission belongs to its Librarian. Shared skill changes go to the LiNKskills Librarian, not an autonomous edit of this immutable release. Keep facts separate from hypotheses, record failure and correction evidence, and identify regression/effectiveness checks where relevant.

## Tooling Protocol and Internal Persistence

Native CLI and reviewed CLI wrapper utilities may inspect bounded authorized artifacts. Direct API and MCP access use existing approved native tools and exact schemas; the abstract `read_file`/`write_file` aliases map to OpenClaw `read`/`write` for approved document artifacts only. `get_tool_details` maps to the supplied native schema/card, not a callable invented alias. If no permitted route exists, use Sara-mediated evidence/output or report the gap.

`state.jsonl` is the Golden Template's portable declaration only. OpenClaw state remains SQLite-owned: use native retained sessions or an explicitly granted Brain checkpoint interface with a trusted task binding. Do not create runtime sidecar state, write another session's private history, or fabricate checkpoint success. The catalog's `execution_ledger.jsonl`/`trace.log` references mean owner telemetry, not permission to create private runtime logs.

## Tools

| Logical capability | OpenClaw route | Boundary |
|---|---|---|
| read_file | `read`, authorized source tool or Sara-provided extract | Approved scoped evidence only |
| write_file | `write` for draft artifacts; Sara-mediated Drive creation | Never runtime state sidecars |
| get_tool_details | Supplied native tool schema/current tool card | No invented callable alias |
| Skill support | `linkskills_use` resource list and exact returned content ID | Exact admitted release |
| Specialist handoff | Sara uses `sessions_send/history/session_status` | Exact enrolled session only |

## Contracts

| Direction | Artifact | Schema |
|---|---|---|
| Input | bounded_task_input | `./references/schemas.json#/definitions/input` |
| Output | task_work_product | `./references/schemas.json#/definitions/output` |
| State | native_checkpoint_projection | `./references/schemas.json#/definitions/state` |

## Progressive Disclosure References

- Detailed variants and exception handling: `advanced/advanced.md`.
- Meaningful fictional examples: `examples/success-pattern.md`, `examples/error-recovery.md`.
- Exact interfaces: `references/api-specs.md`; source/task/merger evidence: `references/source-selection.md`.
- Evaluation cases: `references/eval-suite.json` and `references/eval-suite.yaml`; actual behavior execution remains separate from structural validation.
- Known bad patterns and versioning: `references/old-patterns.md`, `references/changelog.md`.

- Named evidence inputs and completion sections: `references/task-contract-fields.md`.
