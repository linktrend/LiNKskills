---
name: to-tickets
description: "Break the approved PRD into tracer-bullet tickets with blocking edges; this is the feature map."
usage_trigger: "Use in Assembly to produce the feature map from the approved PRD. One GitHub issue is the wrong shape."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [assembly, tickets, feature-map]
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

# To Tickets

Work from the approved PRD. Explore the tree if needed. Prefer prefactor first: make the change easy, then make the easy change.

## Vertical slices

Each ticket is a **tracer bullet**: a narrow complete path through schema/API/UI/tests, demoable alone, sized for one fresh context window. Not a horizontal layer.

Give each ticket **blocking edges**. No blockers means it can start now.

**Wide refactors** are the exception: expand (new form beside old) → migrate batches → contract (delete old). Do not force a blast-radius rename into one tracer bullet.

## Quiz, then publish

For each ticket show title, blocked-by, what it delivers. Ask granularity and edges. Iterate until approved.

Publish **in the plan directory** as one file per ticket, numbered in dependency order:

```
# NN: <title>
What to build: end-to-end behaviour, user perspective
Blocked by: NN titles or None
Status: ready-for-agent
- [ ] acceptance
```

On a real tracker, one issue per ticket with native blocking links if it has them. Do not close the parent PRD. Avoid stale file paths unless a prototype encoded a type or state machine.

Later, `writing-for-agents` fills each ticket with allowed/forbidden files, decided interfaces, local checks, and stop-when-blocked. This skill does not do that fill.

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
