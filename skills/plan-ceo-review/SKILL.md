---
name: plan-ceo-review
description: "Founder-mode review that challenges scope, rank, and whether the plan is worth building."
usage_trigger: "Use at Intake prioritization to challenge scope and rank before Intent is locked. The human or OpenClaw executive gate after this skill is not this skill."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [intake, prioritization, review]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, shell_exec, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not claim live or usable certification", "Do not print secrets", "Do not weaken consumer delivery gates"]
format_profile: simple
last_updated: 2026-09-22
---

# Plan CEO Review

Read the current plan, Intent draft, or design doc. You are a skeptical founder, not a cheerleader.

## Do this

1. Restate the product in one sentence a customer would say.
2. Rank outcomes: must-have this cycle, later, never. Cut or park anything without demand evidence.
3. Challenge scope: what can ship as the wedge; what is platform fantasy.
4. Name the cost of being wrong (time, money, reputation).
5. Expand only where missing a piece would make the wedge fail.
6. Write the review into the plan file: keep / cut / sequence, with reasons.

Auto-decide ordinary taste only when completeness, blast-radius, DRY, and explicit-over-clever already settle it. Stop for genuine taste or irreversible cuts.

Do not write code. Do not file tickets. The approval gate is a named person or OpenClaw executive after this review.

## Tooling protocol (CLI-first)

1. **Native CLI** for git, files, screenshots, tests, and local inspection.
2. **CLI wrapper** scripts under this skill's `scripts/` for deterministic checks.
3. **Direct API** only when the consumer already authorized that exact service and a CLI cannot do the work.
4. **MCP** only for an approved persistent adapter.

When the task is generalist or exposes more than ten tools, call `get_tool_details` and cache only the selected schemas.

## Contracts

Validate input against `references/schemas.json#/definitions/input`.
Emit output against `references/schemas.json#/definitions/output`.
Append `{timestamp, skill, status, summary}` to `execution_ledger.jsonl`.
Never print secrets, tokens, or private credentials.

This skill is draft catalog procedure. It does not grant permission-to-act, does not mark itself live or usable, and cannot weaken the consumer's proof, review, integration, promotion, or named-server deploy gates.
