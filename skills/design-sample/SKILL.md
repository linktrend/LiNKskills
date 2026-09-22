---
name: design-sample
description: "Lock pictures or a small picker the builders must match. Required in Assembly when the product has a screen."
usage_trigger: "Use in Assembly after visual direction is locked and before execution briefs. Builders must match this sample and must not restyle later."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [assembly, sample, design]
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

# Design Sample

Required when the product has a screen. Lock **one** set of pictures or a small picker. Write the lock into every screen issue brief.

## Direction must already be locked

Read company brand notes, then `taste-design-exploration`, then a named look only if the plan allows it. Do not explore here.

## Image comps (Taste)

For web: one horizontal frame per section, image-only. For mobile: screens/flows, image-only. No code in the comps. If the product is identity-only, brand-kit boards (logo, palette, type, applications) during Intent instead.

## Picker (Emil prototype)

When more than one layout must be compared: 3–5 **divergent** isolated variants behind a **fixed picker**. Same content. No production wiring. Pick one. Delete the losers.

## Image-to-code

Only after a picture is chosen: analyze the reference, then implement to match in Execution via `impeccable-design-system`, not in this skill.

Output: paths to locked images or picker, tokens they imply, motion yes/no, components builders may use. The sample is the look.

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
