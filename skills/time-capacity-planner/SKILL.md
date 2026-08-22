---
name: time-capacity-planner
description: "Turns a person's confirmed and provisional work into dependency-aware plans that fit an approved capacity calendar."
usage_trigger: "Use when an operator gives a task list, asks for time organisation, or needs work scheduled around capacity periods."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-19
author: LiNKskills Library
tags: [planning, dependencies, capacity, tasks, calendar]
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
permissions: [fs_read, fs_write]
scope_out: ["Do not silently commit inferred work", "Do not mutate tasks or calendars without the consumer's authority", "Do not claim completion without evidence"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
format_profile: heavy
last_updated: 2026-08-19
---

# Time Capacity Planner

This is a reusable planning skill. The consuming agent supplies the operator
identity, timezone, task system, calendar system, capacity periods, review
periods, and authority grants. Never place private account details in this
skill or infer them from a task description.

## Tooling protocol

Classify the request as `specialist` or `generalist`. Use native CLI first,
then a narrow CLI wrapper, then a direct API only for an approved exception,
and MCP only for a persistent service. For a generalist request or more than
ten tools, load tool details before planning. This skill does not authorize any
of those tools.

## Decision tree

1. Resume the same task from `.workdir/tasks/{{task_id}}/state.jsonl` when it
   exists.
2. Classify each item as `confirmed`, `provisional`, `blocked`, or
   `awaiting-information`. An explicit assignment is confirmed. A task merely
   inferred from conversation is provisional until the operator confirms it.
3. Capture title, owner, desired result, deadline, importance, difficulty,
   estimated capacity periods, dependencies, evidence required, and authority.
   Label estimates and allow the operator to override them.
4. Ask only questions whose answer could change owner, deadline, dependency,
   safety, authority, or the number of periods. Read-only research is allowed;
   external commitments are not.
5. Order work by hard deadlines and prevention, dependency-unblocking, the
   current outcome, routine maintenance, then optional improvements. Fit work
   to the supplied capacity profile and protect fixed commitments.

## Capacity rules

- Use the consumer's configured difficulty mapping. A common mapping is easy
  work first, medium work second, and hardest work third; do not override a
  supplied profile.
- A flexible period remains work time while material operator work is
  outstanding. It becomes personal time only after the work queue is current,
  unless the operator overrides this.
- Group related small tasks. Group unrelated small tasks only when no suitable
  alternative remains. Split large work into connected child results and retain
  the parent/child link in the ledger.
- Reduced capacity requires asking whether the operator wants time off and for
  how long. Without time off, schedule easier work more slowly. Unavailable
  capacity protects only hard commitments. Recovered capacity needs an explicit
  confirmation before normal planning resumes.

## Outputs and authority

The plan states what is known, what is estimated, dependencies, periods,
owners, evidence, and open questions. The consumer decides whether to write
operator Tasks or Calendar events. Use a numbered, mobile-readable email for a
large plan; every decision includes the matter, recommendation, reason,
choices, and `Other — specify`. Never use LiNKskills as an authorization plane.
Only the consumer's Program Ledger or capability grant may authorize a write.

Completion states distinguish `ready`, `scheduled`, `in-progress`, `blocked`,
`awaiting-operator-confirmation`, `awaiting-agent-evidence`, and `completed`.
Lisa or another agent's words are not completion evidence; the consumer must
check the required receipt, artifact, test, or external record.

## Workflow

1. Write `INITIALIZED` with the input sources and profile identifier.
2. Build the task/dependency graph and record assumptions.
3. Research or request only material missing facts.
4. Produce the plan and multiple-choice decisions, or checkpoint
   `PENDING_APPROVAL` when a material ambiguity remains.
5. Persist scheduling decisions and the evidence requirements.
6. On later review, reconcile actual evidence with the plan and keep unfinished
   work visible rather than silently dropping it.
7. Write `COMPLETED` only after output-contract validation.

## Contracts

| Direction | Artifact | Schema |
| --- | --- | --- |
| Input | `planning_request` | `./references/schemas.json#/definitions/input` |
| Output | `capacity_plan` | `./references/schemas.json#/definitions/output` |
| State | `planning_state` | `./references/schemas.json#/definitions/state` |

## Progressive disclosure

- Read `references/api-specs.md` for input/output fields.
- Read `references/old-patterns.md` before finalising a plan.
- Read `advanced/advanced.md` only for large dependency graphs or four-week
  plans.
