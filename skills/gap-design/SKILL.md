---
name: gap-design
description: "Design remaining technical gaps as documents: deep-module vocabulary, DESIGN.md consultation, and plan-time UI scoring when there is a screen."
usage_trigger: "Use in Assembly after library lookup to design remaining gaps. Documents only: no throwaway prototypes or shotgun mockups."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [assembly, design, architecture]
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

# Gap Design

Documents only. Skip throwaway HTML prototypes and design-shotgun variants. Screen look is `taste-design-exploration` then `design-sample`.

## Deep modules (Matt)

Use these words exactly: **module**, **interface**, **implementation**, **depth**, **seam**, **adapter**, **leverage**, **locality**.

- Deep: lots of behaviour behind a small interface.
- Deletion test: if deleting the module spreads complexity across callers, it was earning its keep.
- The interface is the test surface.
- One adapter is a hypothetical seam; two adapters make it real.
- Accept dependencies; do not construct them inside the module.
- Prefer existing seams. New seams at the highest point that stays deep.

Write the gap design with: modules to add or deepen; interfaces; seams to test; adapters; what stays shallow on purpose.

## DESIGN.md consultation (gstack)

If the product has a screen and no locked visual system, propose tokens, type, spacing, components, and states in `DESIGN.md`. Honor company brand notes first. Do not restyle after `design-sample` locks pictures.

## Plan-time UI scoring (when there is UI)

Score 0–10: hierarchy, empty/error/loading, accessibility, match to the forthcoming sample. Must-fix items go into issue briefs. Do not implement.

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
