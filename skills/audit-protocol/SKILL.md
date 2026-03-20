---
name: audit-protocol
description: "Enforces predictive auditing so intent is logged before any write-action across Google Workspace and n8n operations."
usage_trigger: "Use when a task writes data to Google Workspace services or n8n workflows and requires pre-write intent logging."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-24
author: LiNKskills Library
tags: [audit, compliance, observability]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-4.1
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [gws, ltr, n8n]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not execute write actions without pre-write intent logs", "Do not suppress failed intent audit entries"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-24
---

# audit-protocol

## Decision Tree (Fail-Fast & Persistence)
0. Resume from `.workdir/tasks/*/state.jsonl` if task is active.
1. Confirm engine intelligence floor.
2. Confirm tooling policy terms: native cli, cli wrapper, direct api, mcp.
3. Classify run as Specialist or Generalist and use `get_tool_details` for Generalist.
4. Before any write action, emit predictive intent log.
5. Block execution if intent log cannot be written.

## Predictive Auditing Rule (Mandatory)
Before any write-action in `gws`, `ltr`, or `n8n`, agent must log intent through `LTRAuditLogger`:
- Service
- Action
- Target resource
- Expected effect
- Planned rollback cue

This intent entry must be written **before** calling the write command.

## Tooling Protocol (CLI-First)
1. Native CLI for checks and log validation.
2. CLI wrappers for service actions.
3. Direct API only for exception cases.
4. MCP only for persistent session workflows.

## Internal Persistence (Zero-Copy / Flat-File)
- Write phase checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save intent and execution traces under task-local flat files.
- Use seek-based reads to reduce context load.

## Smart JIT Tool Loading (Mitigated)
- JIT only for Generalist or >10 tools.
- Must call `get_tool_details` and cache capability summaries.

## Workflow
### Phase 1: Ingestion & Checkpointing
- Identify all planned write actions.
- Validate input contract.
- Checkpoint `INITIALIZED`.

### Phase 2: Intent Drafting
- Generate intent payload per planned write action.
- Validate intent fields and checkpoint `IN_PROGRESS`.

### Phase 3: Intent Logging Gate
- Write intent to `LTRAuditLogger` before write action.
- If log write fails, set `FAILED` and stop.

### Phase 4: Action Execution
- Execute write action only after confirmed intent log.
- Validate outputs and checkpoint `COMPLETED`.

### Phase 5: Self-Correction
- Append ledger entry, persist trace log, and update old patterns.

## Contracts
- Input: `./references/schemas.json#/definitions/input`
- Output: `./references/schemas.json#/definitions/output`
- State: `./references/schemas.json#/definitions/state`
