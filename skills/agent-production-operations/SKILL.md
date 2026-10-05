---
name: agent-production-operations
description: "Monitor approved production agent evidence and prepare an evidence-linked runtime operating plan for quality, cost, latency, tool health, escalation and trace-to-eval feedback."
usage_trigger: "Use for ongoing operational status or a staged-control proposal for an existing evaluated production agent; do not use for build/eval design, postmortem, or technical runtime execution."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [agents, production-operations, quality-monitoring, task-specific]
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
scope_out: ["No authority grant, rollout, traffic/config/runtime mutation, shutdown or external notification", "No invented baseline, threshold, business policy, or evaluation result"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Agent Production Operations

## Role

Prepare evidence-grounded monitoring reports and control proposals for an existing agent. Sara owns task/business-status analysis; Eric owns technical runtime/evidence interfaces and changes. The Librarian owns catalog/eval-suite admission; incident-learning owns postmortems.

## Workflow

Follow `advanced/advanced.md`. Identify agent/version, cohort, measurement window, source/threshold owner, and available evidence before comparing performance. Keep task quality separate from tool success, service levels, cost and authority compliance. Return a concrete report/proposal with evidence, uncertainty, owner routes and capability gaps.

## Tool protocol and state

Map abstract `read_file` to native `read` on a known authorized path; `write_file` to native `write`/`edit` only for an approved report artifact; `get_tool_details` to inspection of the current native schema and owner toolcard; `list_dir` is not callable. Use a native CLI, CLI wrapper, direct API, or MCP only when the exact callable operation appears in the current native schema and owner toolcard. If not available, use supplied evidence and report the exact gap. Never run source scripts, shell commands, or guessed runtime API. OpenClaw runtime state remains SQLite-backed; checkpoints use the supported consumer owner interface, never local JSONL.

## Contract

Input: `references/schemas.json#/definitions/input`; output: `references/schemas.json#/definitions/output`; state: `references/schemas.json#/definitions/state`. Detailed task method: `advanced/advanced.md`. Exact upstream tree/notices: `references/upstream/SOURCE-MANIFEST.json`.

This Specialist workflow can analyze real approved traces/metrics when evidence and native read interfaces are available. It cannot perform runtime control changes or send notifications.
