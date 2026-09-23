---
name: canary
description: "Watch the first minutes on the named production server after deploy: health, console, screenshots, regressions."
usage_trigger: "Use immediately after land-and-deploy on the named live URL."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [shipment, canary]
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

# Canary

Release reliability on the **named live URL**. Default 10 minutes. Range 1–30 minutes. `--quick` is one pass. `--baseline` is before deploy only.

## Setup

Create a report folder in the consumer proof directory (not a secret store). Parse URL, duration, pages.

## Baseline mode

For each page: load, capture screenshot, console errors, load timing, text snapshot, 404 link check. Save manifest. Stop: deploy, then run watch mode.

## Watch mode

Discover pages from nav or `--pages`. Each round: screenshot, console identity (not just count), load time, broken links, text disappearance vs baseline. Continue until duration elapses or a blocker fires (blank page, error burst, health fail).

Write the canary report. On failure, hand to `land-and-deploy` revert. Do not "fix live" by SSH unless the plan's deploy method says so.

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
