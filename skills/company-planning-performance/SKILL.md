---
name: company-planning-performance
description: "An evidence-bounded planning and performance review method for company horizons, objectives, KPI variance, delivery signals, and owner-reviewed reprioritization."
usage_trigger: "Use for synthetic, redacted, or public planning evidence when a consumer needs a concise horizon plan, KPI review, forecast-versus-actual comparison, blocker/late/obsolete detection, or evidence-backed reprioritization draft without mutating Program or Task state."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [planning, performance, objectives, kpis, forecasting, evidence]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5.6-luna
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [executive-decisions-governance]
permissions: [fs_read, fs_write]
scope_out: ["Do not approve, activate, schedule, send, or enforce a plan or reprioritization", "Do not create or mutate Program, project, objective, KPI, milestone, calendar, or Task state", "Do not invent forecast, actual, target, status, precision, owner, or completion facts", "Do not call connectors, expose credentials, retain private company data, or include customer records in fixtures or telemetry"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-08-24
---

# Company Planning and Performance

This skill turns supplied planning evidence into a compact, reviewable planning
artifact. It is a drafting and comparison method, not a planning database,
Program Ledger, task manager, scheduler, forecasting authority, or performance
system. The consumer and named owner retain all authority and mutable state.

## Planning contract

1. Select exactly one supported horizon: monthly, rolling four-week, quarterly,
   annual, three-year, or five-year. Keep the horizon and period explicit.
2. Give each objective and KPI a stable reference. Link every material KPI
   target, forecast, actual, or status signal to supplied evidence.
3. Compare forecast with actual only when both are supplied with the same unit,
   period, and evidence. Otherwise report `not_reported`, `unknown`, or
   `not_comparable`; never manufacture precision or fill gaps with a model guess.
4. Surface late, blocked, obsolete, and on-track signals as evidence-backed
   observations. A signal is not a command to alter a Program or Task.
5. Reprioritization is a proposed owner-review record. It requires a rationale,
   affected objective references, and evidence; it never activates, schedules,
   approves, or mutates anything.

## Authority and safety boundary

The helper returns `READY_FOR_OWNER`, `DRAFT`, or `BLOCKED` and always emits
empty effects. Requested actions such as `approve`, `activate`, `schedule`,
`send`, `create_task`, or `mutate_program` fail closed. Supplied owner decisions
remain evidence only. Private identifiers, credentials, customer records, and
confidential company text are rejected without echoing their contents.

## Horizon and performance semantics

Monthly and rolling four-week views support near-term operating review;
quarterly and annual views support objectives and KPI commitments; three-year
and five-year views support directional strategy. Long-range views must be
marked directional when numeric evidence is absent. A forecast is not an
actual, a target is not a result, and a late or blocked signal is not proof of
failure. Use the exact `Other — specify` escape hatch for non-exhaustive
planning choices.

## Tooling, ownership, and progressive disclosure

Use the native CLI first, a CLI wrapper for deterministic normalization, direct API
only through a consumer-owned exception adapter, and MCP only for a
consumer-authorized persistent session. This skill owns no connector,
credential, calendar, Program, Task, KPI store, or transport binding. Read the
contracts in [`references/schemas.json`](references/schemas.json#/definitions/input)
and [`references/schemas.json`](references/schemas.json#/definitions/output), the field
rules in [`advanced/advanced.md`](advanced/advanced.md), the overlap record in
[`references/api-specs.md`](references/api-specs.md), and the canonical eval
suite before release. A specialist or generalist execution profile must retain
only redacted state in `state.jsonl`; no raw private input or transport payload
is persisted.
