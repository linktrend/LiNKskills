---
name: personal-compliance-tracker
description: "Tracks configured personal check-ins, charging or threshold obligations, and time-window compliance without duplicate reminders."
usage_trigger: "Use when a consumer needs a private ledger, periodic check-ins, threshold prediction, or conditional reminders for a person's routine."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-19
author: LiNKskills Library
tags: [compliance, battery, reminders, check-ins, private]
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
scope_out: ["Do not guess from stale measurements", "Do not duplicate reminders already owned by Calendar", "Do not expose private check-in data in work reports"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
format_profile: heavy
last_updated: 2026-08-19
---

# Personal Compliance Tracker

This skill is a reusable ledger and evaluator. The consumer supplies the
private subject, timezone, check-in schedule, threshold rules, notification
channel, and storage authority. Keep those bindings outside this shared skill.

## Tooling protocol

Classify the request as `specialist` or `generalist`. Use native CLI first,
then a narrow CLI wrapper, then a direct API only for an approved exception,
and MCP only for a persistent service. For a generalist request or more than
ten tools, load tool details before planning. This skill does not authorize any
of those tools.

## Decision tree

1. Resume the same task state when present; otherwise create an idempotent
   ledger cycle for the consumer's calendar date.
2. Record every check-in with timestamp, reported values, status, source,
   measurement context, and any routine change. Preserve corrections instead
   of overwriting the original observation.
3. For a threshold prediction, use only fresh, context-matched observations.
   Recalculate rates from usable non-plateau data. A configured display maximum
   is not evidence of a charge or discharge rate.
4. Evaluate whether the threshold will be reached before the next configured
   charging or recovery window. If yes, create one idempotent delivery intent;
   the consumer's channel owner delivers it. If data is stale or insufficient,
   request a fresh check-in instead of guessing.
5. For time-window obligations, classify reports using the consumer's exact
   window: on-time, late, or missed. Reset only at the configured boundary.

## Reminder discipline

- Use the configured reminder times and send only the conditional reminders
  that the ledger says are still needed.
- If an obligation already has a Calendar event, Calendar owns the reminder;
  do not send a duplicate agent reminder.
- The hourly evaluator (when configured) is a calculation pass, not a second
  heartbeat mechanism and not permission to interrupt unrelated maintenance.
- Keep delivery receipts separate from the private ledger. A planned intent is
  not a delivered alert.

## Privacy and authority

Detailed observations stay in the consumer's private store. LiNKskills does
not grant access to messages, accounts, health records, or devices. The skill
may expose only a consumer-approved coarse state to a work planner, such as a
capacity signal. Channel delivery, account access, and external writes remain
with the consuming Program's authority plane.

## Workflow and contracts

1. Checkpoint `INITIALIZED` with cycle date and rule-set version.
2. Ingest or request the check-in; validate source and time window.
3. Update the ledger append-only and compute the next expected check.
4. Emit at most one delivery intent when the threshold rule requires it.
5. Validate output and checkpoint `COMPLETED`; otherwise retain a retryable
   state and surface the exact reason.

| Direction | Artifact | Schema |
| --- | --- | --- |
| Input | `compliance_request` | `./references/schemas.json#/definitions/input` |
| Output | `compliance_result` | `./references/schemas.json#/definitions/output` |
| State | `compliance_state` | `./references/schemas.json#/definitions/state` |

Read `references/api-specs.md` for the rule configuration and
`references/old-patterns.md` before changing a threshold workflow.
