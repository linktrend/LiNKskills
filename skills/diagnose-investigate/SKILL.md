---
name: diagnose-investigate
description: "Find a cause before any fix: tight red command first, then a written root cause. Then return to implement."
usage_trigger: "Use when Execution or Verification repair needs a cause. No fix without investigation."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [repair, debug]
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

# Diagnose Investigate

Iron law: **no fix without a cause**. Redact secrets as `<REDACTED>`.

## Matt — tight red loop first

Spend almost all effort building **one command** you have already run that:

- is **red-capable** on the user's exact symptom
- is deterministic (or a high flake rate you raised on purpose)
- is fast
- is agent-runnable

Order of construction: failing test; curl/HTTP; CLI fixture; headless browser; replay a captured trace; throwaway harness; fuzz; bisect; differential; last-resort HITL script.

If you cannot build a loop, stop and list what you tried. Do not hypothesise.

Then reproduce, minimise inputs one cut at a time, then hypothesise.

## gstack — written root cause

After the loop is red, write: **Root cause hypothesis:** a specific testable claim. Name the module. Lock edits to that directory if the consumer uses a freeze boundary. Do not patch elsewhere.

OpenClaw hosts use the same iron law.

Then return to `implement` with the red command as the proof. Do not "also fix" unrelated issues.

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
