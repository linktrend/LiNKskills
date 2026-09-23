---
name: autoplan
description: "Run CEO, design, DX, and eng plan reviews in order with auto-decisions; eng last so a test plan exists for Verification."
usage_trigger: "Use for independent review of the Technical PRD. Eng is always last. Do not re-run this whole chain on Assembly design."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [intake, review, autoplan]
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

# Autoplan

Read the PRD and design doc. Run phases in order. Do not skip eng. Taste decisions wait for one final gate.

## Decision principles (auto-answer ordinary intermediates)

1. Choose completeness. 2. Fix the blast radius. 3. Pragmatic cleaner option. 4. DRY — reject duplicates. 5. Explicit over clever. 6. Bias toward action — flag, do not stall.

CEO phase: completeness and blast radius win ties. Eng phase: explicit and DRY win. Design/DX: stop for genuine taste.

## Phase 0 — Detect surfaces

UI in the PRD? Developer-facing API/CLI/SDK/docs? Record both.

## Phase 1 — CEO

Run `plan-ceo-review` procedure on this artifact: keep/cut/sequence.

## Phase 2 — Design (only if UI)

Score the plan 0–10 on hierarchy, information architecture, empty/error states, accessibility, and whether a locked sample will be required. Edit the plan with must-fix items. Do not invent pixels; that is `taste-design-exploration` and `design-sample`.

## Phase 2.5 — DX (only if developer surface)

Score onboarding time, command/API clarity, error messages, and docs shape.

## Phase 3 — Eng (always)

Architecture fit, seams, risks, rollout, and a **test plan** Verification will read: acceptance criteria → checks, data, environments, out-of-scope tests.

## Phase 4 — Final gate

Aggregate unresolved taste/irreversible items. Stop for a named person or OpenClaw executive. Write the review into the plan directory.

In-package section files under `references/autoplan/` hold the long scoring tables. Follow them when scoring; do not open an external gstack install.

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
