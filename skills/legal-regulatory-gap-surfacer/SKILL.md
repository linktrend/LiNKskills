---
name: legal-regulatory-gap-surfacer
description: "Prepare evidence-linked regulatory gap intake, deduplication, and owner-notice proposals from an authorized policy diff."
usage_trigger: "Use when a verified or candidate policy diff needs review for gap-register intake, deduplication, or a draft owner notice."
version: 0.1.1
release_tag: v0.1.1
created: 2026-10-04
author: LiNKskills Library
tags: [legal, regulatory, gap-intake, task-specific, draft]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, list_dir, get_tool_details, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No legal conclusion, policy approval, register write, close/accept decision, notification, publication, or official action.", "No invented law, dates, company facts, owners, thresholds, or tracker configuration.", "No source scripts, shell commands, APIs, or connector aliases are callable tools.", "Do not treat a scope-limited source diff as a complete regulatory gap review."]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-05
---
# Regulatory Gap Intake and Surfacing Proposals

## Role and purpose

Prepare a bounded, evidence-linked proposal for adding or deduplicating regulatory gaps from an authorized policy diff, with optional draft owner-notice text. This task does not report the full gap register or decide that an existing gap is closed/accepted; route those requests to `legal-regulatory-gaps`.

## Native tools and persistence

**Runtime persistence precedence.** The frontmatter `persistence.state_path` is portable template metadata, not an instruction to create a JSONL runtime file. In OpenClaw, checkpoint through the supported consumer-owned SQLite interface. Do not create `state.jsonl`, JSONL sidecars, or JSON runtime state. If the approved checkpoint interface is unavailable, keep the checkpoint reference in the named work product and disclose that limitation.


This heavy profile distinguishes **Specialist** (one domain, at most ten tools) from **Generalist** (cross-domain or over ten tools). Native CLI, CLI wrapper, direct API and MCP are routing categories, not proof that Sara has such an interface. Use `get_tool_details` only if that exact current tool exists. The contract names `state.jsonl` for resumability; checkpoint only through an authorized consumer-owned route. If unavailable, disclose that limitation and do not create a local runtime sidecar.

Task-specific contracts are in `references/schemas.json#/definitions/input`, `#/definitions/output`, and `#/definitions/state`.

Use only supplied/authorized policy-diff and register snapshots. No automatic register changes, close/accept decisions, recipient lookup, or message sending. Active procedure: `advanced/advanced.md`; contracts: `references/schemas.json`; source and exact license hashes: `references/upstream/SOURCE-MANIFEST.json`.
