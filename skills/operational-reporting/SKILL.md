---
name: operational-reporting
description: "Builds concise evidence-backed operational digests, flash reports, numbered plans, and periodic work reports for an approved audience."
usage_trigger: "Use when an operator needs a recurring digest, status flash, decision plan, or period report assembled from verified work sources."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-19
author: LiNKskills Library
tags: [reporting, digests, decisions, operations, evidence]
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
scope_out: ["Do not include private health or private compliance detail in work reports", "Do not report unverified completion", "Do not claim delivery without a channel receipt"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
format_profile: heavy
last_updated: 2026-08-19
---

# Operational Reporting

This skill is a reusable report composer. The consumer supplies the timezone,
report deadlines, source calendars, task systems, message channels, audience,
and privacy policy. Lisa-specific destinations and schedules are bindings, not
library content.

## Tooling protocol

Classify the request as `specialist` or `generalist`. Use native CLI first,
then a narrow CLI wrapper, then a direct API only for an approved exception,
and MCP only for a persistent service. For a generalist request or more than
ten tools, load tool details before planning. This skill does not authorize any
of those tools.

## Decision tree

1. Resume the same report state when present and identify the reporting window
   from the configured deadline, not from an assumed start time.
2. Read only the configured sources and label each fact by source and freshness.
   Separate the operator's task system from subordinate-agent work,
   commitments, and other task sources.
3. Include only the configured calendar classes. Exclude routine or private
   calendars when the consumer says so. Include only messages that require the
   audience's attention, decision, or action; do not dump an inbox.
4. Require checked evidence for Lisa or subordinate-agent completion. The
   operator's own completion report may be accepted when the consumer policy
   says so; other claims need the required artifact, test, or receipt.
5. Render the configured mobile format. Use short headings and bullets rather
   than a dense table. A flash report may include a configured status line such
   as battery status without revealing private measurements.
6. Send through every configured destination and record each channel receipt.
   A rendered message is not proof of delivery.

## Report modes

- **Executive digest:** same structure at each configured morning/evening
  deadline: since the previous digest, until the next digest, decisions needed,
  outstanding work, relevant calendar events, task separation, supervised-agent
  evidence, and maintenance result.
- **Flash report:** compact status, completed/in-progress/blocked work,
  decisions, next result, configured status lines, and flexible-period decision.
- **Numbered plan:** email for long plans; each item has a stable number, matter,
  recommendation, reason, choices, and `Other — specify`.
- **Periodic work report:** completed work since the previous report,
  outstanding work, decisions, risks, and expected work until the next report.

Keep private health, medication, selfies, detailed battery data, and private
calendar content out of work reports. LiNKskills observes report assembly; it
does not decide whether a consumer may send a message or change a calendar.

## Workflow and contracts

1. Checkpoint `INITIALIZED` with report mode and reporting window.
2. Gather and validate source receipts; mark missing or stale sources.
3. Compose, deduplicate, and apply the configured redaction policy.
4. Set `PENDING_APPROVAL` when a required source or decision is missing.
5. Deliver only through authorized consumer channels and record receipts.
6. Checkpoint `COMPLETED` only after output and receipt validation.

| Direction | Artifact | Schema |
| --- | --- | --- |
| Input | `report_request` | `./references/schemas.json#/definitions/input` |
| Output | `operational_report` | `./references/schemas.json#/definitions/output` |
| State | `report_state` | `./references/schemas.json#/definitions/state` |

Read `references/api-specs.md` for the mode fields and
`references/old-patterns.md` before changing a report template.
