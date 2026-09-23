---
name: land-and-deploy
description: "Merge or land the reviewed release, deploy to the named production server, and confirm it is up."
usage_trigger: "Use after ship, when the plan names the server and deploy method. A cheaper model must not invent where it ships."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [shipment, deploy]
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

# Land And Deploy

The plan must name **the server** and **the deploy method**. If either is missing, **stop**.

## Always stop for

First-run dry-run of the named method; pre-merge/pre-land readiness; missing credentials; CI red; merge conflicts; deploy failure; failed health check.

## Sequence

1. Narrate. Authenticate the named forge CLI if merge is in the plan.
2. Find the PR/MR or the already-integrated trunk SHA the plan names.
3. Readiness: reviews, named gates, Verification proof on that SHA. Consumer gates win over gstack defaults.
4. Land: merge only if this consumer's delivery controller/packager owns merge. Implementer sessions do not self-merge. If you are the authorized ship runner, merge with the repo's method.
5. Deploy with the **plan's method** to the **named server** (not a guessed host). Wait for the named health endpoint.
6. Record URL, SHA, time, health result.

If health fails, offer revert using the plan's rollback, do not invent one.

Settings that can only be made after live still happen on this path, not by a person on the machine.

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
