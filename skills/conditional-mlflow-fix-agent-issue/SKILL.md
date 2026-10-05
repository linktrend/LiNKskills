---
name: conditional-mlflow-fix-agent-issue
description: "Prepare a bounded repair plan for a reproduced agent defect with owner-approved trace and repository/tool access."
usage_trigger: "Prepare a bounded repair plan for a reproduced agent defect with owner-approved trace and repository/tool access."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [mlflow, conditional, technical-library]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 48000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, list_dir, get_tool_details, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No automatic tool, package, account, connection, legal filing, or external action", "No invented facts, authority, jurisdiction, or capability"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Conditional MLflow Agent Issue Repair

## Role and trigger

Prepare a bounded repair plan for a reproduced agent defect with owner-approved trace and repository/tool access.

## Conditional use boundary

Conditional on Eric-owned backend selection and currently visible native tool capabilities; no MLflow runtime or optional service is installed or claimed.

## Procedure

Read `advanced/advanced.md` for this task card. Inspect only the known source paths and evidence refs supplied by the task. Abstract `read_file` maps to native `read` on a known path; `write_file` maps to native `write`/`edit` only for an explicitly approved artifact; `get_tool_details` means inspect the current native schema and owner toolcard; `list_dir` is not callable. If the native interface is absent, record the exact capability gap and stop before invoking it. No shell helper, hidden CLI alias, or guessed API.

Checkpoint via the consumer owner interface; OpenClaw runtime state remains SQLite-backed.

## Native protocol compatibility

Use the native cli, cli wrapper, direct api, or mcp only when that exact callable appears in the current native tool schema and owner toolcard; otherwise the specialist returns a capability gap. No abstract alias is callable.

## Contract

Input/output fields are defined in `references/schemas.json`. Original source and file hashes are in `references/upstream/SOURCE-MANIFEST.json`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
