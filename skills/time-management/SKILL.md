---
name: time-management
description: "Plans confirmed and provisional work from intake through monthly reporting without owning consumer task state."
usage_trigger: "Use when the consumer needs store-independent intake, prioritisation, capacity planning, review, evidence reconciliation, or a standing-rule proposal."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [planning, tasks, capacity, evidence, reviews]
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
dependencies: [company-communication]
permissions: [fs_read, fs_write]
scope_out: ["Do not own mutable task state or SQLite", "Do not send, schedule, commit, activate, or make consequential changes", "Do not infer acknowledgement or completion", "Do not include health causes in capacity outputs"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
format_profile: heavy
last_updated: 2026-08-24
---

# Time Management

A store-independent reasoning contract for the consumer-owned time-management
system. OpenClaw's agent-scoped private SQLite store mints permanent `T-`
references and owns mutable state. Google Tasks, Brain, Program Ledgers,
Calendar, email, Telegram, browser chat, and handoffs retain their own opaque
references; this skill only maps supplied references and returns a plan.

## Intake and authority

1. Accept direct Principal instructions and other authorised conversation
   sources as `Confirmed`; detected possible actions remain `Provisional`.
2. Capture a short receipt before reasoning: source, timestamp supplied by the
   consumer, confirmation, desired result, owner, importance, difficulty,
   estimated periods, deadline, dependencies, unlocks, mappings, and evidence.
3. Read-only provisional research is allowed. External communication, spending,
   commitment, task/calendar writes, and consequential action require the
   owning consumer authority. A plan never grants that authority.
4. Preserve stable `T-` IDs and every supplied Google/Brain/Program/email or
   handoff mapping. Never mint an ID in LiNKskills' own store.

Materially missing authority or evidence checkpoints as `PENDING_APPROVAL`;
preserve confirmed work and ask the smallest decision-changing question.
The helper performs read-only evaluation and returns no side effects.

## Priority, planning, and status

Prioritise concrete harm or immovable deadlines, then dependency-unblocking,
the most important weekly outcome, routine/maintenance, and optional
improvements. Difficulty selects a suitable period; it does not define
importance. Protect fixed events, breaks, and protected work periods.

Permitted statuses are `Provisional`, `Ready`, `Scheduled`, `In progress`,
`Waiting`, `Blocked`, `Awaiting Carlos's update`, `Awaiting for other`,
`Verified complete`, `Completed — Carlos reported`, `Cancelled`, `duplicate`,
and `created by mistake`. Lisa/subordinate completion requires evidence and a
verification result. The Principal's own completion report is accepted. Silence
is delivered/not-started, never acknowledgement.

## Capacity and review

Use the supplied capacity state (`high`, `normal`, `reduced`, `unavailable`, or
`recovered`) and periods. Reduced or unavailable capacity asks whether and how
much time off is wanted; without that answer, recommend easier/slower work.
Recovered capacity is temporary until replanning. A flexible period becomes
personal time only when there is no overdue work, suitable ready work,
resolvable blocker, at-risk deadline/outcome, or useful action before the next
workday. Capacity reasoning never records a health cause.

The weekly plan fully allocates the current Monday–Friday week and gives future
weeks warnings or preparation only. The Monday plan is a mobile-friendly email
without tables; omit empty sections. A morning review confirms or replans periods,
tasks, decisions, and assignments. An evening review records completed, partial,
blocked, and not-started work, reasons, deliberate reschedules, and estimate
updates. An end check is conditional on the result not already being known.
Monthly reports retain `T-` IDs, cover the prior and next reporting windows,
and omit minor-task dumps.

## Standing rules and tooling

A standing-rule proposal states its trigger, automatic action, exceptions,
affected agents/systems, and permanence/review date. It is never activated by
this skill. Classify the request as specialist or generalist, then follow native CLI, then a narrow CLI wrapper, approved direct API
exception, and MCP only for a persistent service. Read progressive-disclosure
references before complex four-week plans. Persist checkpoints but keep the
release effect-free and free of real private data.

## Contracts

| Direction | Artifact | Schema |
| --- | --- | --- |
| Input | `planning_request` | `./references/schemas.json#/definitions/input` |
| Output | `time_management_result` | `./references/schemas.json#/definitions/output` |
| State | `planning_state` | `./references/schemas.json#/definitions/state` |

## Migration boundary

`department-head` contributes supervision reasoning and `task-decomposition`
contributes atomic verification reasoning. Their generic releases remain
separate and immutable; this canonical family does not duplicate their stores
or authority. The older `time-capacity-planner` is migration provenance, not a
consumer state owner.
