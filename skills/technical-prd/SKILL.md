---
name: technical-prd
description: "Turn approved Intent into an executable technical spec: five-phase precision plus in-repo spec, seams, and tracker publish."
usage_trigger: "Use at Intake to produce the Technical PRD after Intent. Do not spawn Execution from this skill."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [intake, prd, spec]
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

# Technical PRD

Do not interview from zero if `grill-office-hours` already ran: synthesize, then fill remaining holes. Do not run `spec --execute`. Do not treat one GitHub issue as the later feature map.

## Phase 1 — Why

Answer all five without hand-waving: who is affected; current behaviour (verified); desired behaviour; why now; how we know it is done (observable).

## Phase 2 — Scope

Lock: explicit out of scope; systems touched; ordering constraints; smallest version that delivers the value; failure modes and rollback.

## Phase 3 — Technical interrogation

Read code before asking. Cite `path:line`. Categories that apply: data model, API, background jobs, UI, infrastructure, testing. Do not ask what the tree already answers. Greenfield: say you searched and found nothing.

## Phase 4 — Draft

Present the full PRD. Ask what is wrong. Iterate until confirmed.

Matt template inside the PRD:

- Problem statement (user perspective)
- Solution (user perspective)
- Extensive user stories (`As an … I want … so that …`)
- Implementation decisions (modules, interfaces, schema, APIs — not stale file paths unless a prototype encoded a type/state machine)
- Testing decisions: good tests verify external behaviour; name seams; name prior art in-repo
- Out of scope
- Further notes

## Phase 4.5 — Quality gate

Semantic review: every acceptance criterion is observable. Fail-closed redaction: no secrets in the PRD. If a score gate exists, run it; never skip redaction.

## Phase 5 — Publish in-repo

Write the PRD in the plan directory. Optionally file a tracker issue that **points at that file**. Label it ready for review, not ready-to-implement-by-spawning. Tickets come from `to-tickets`.

Question rounds: 3–5 numbered questions, assumptions explicit, code cited.

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
