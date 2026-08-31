---
name: hybrid-development-methods
description: "Routes software-development work through LiNKtrend's exact combined gstack macro workflows and Matt Pocock micro workflows while remaining subordinate to each consumer's delivery process."
usage_trigger: "Use when IDE Development, LiNKdeveloper, or another software consumer needs specification, PRD clarification, issue decomposition, TDD, debugging, architecture improvement, project health, QA, review, retrospective, context continuity, or shipping assessment."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [development, gstack, mattpocock, specification, tdd, debugging]
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
scope_out: ["Do not load gstack and Matt Pocock routes that perform the same operation", "Do not let gstack ship bypass consumer proof, review, integration, or promotion gates", "Do not reintroduce sunset duplicates as competing authorities", "Do not auto-refresh adapted source bytes from upstream"]
format_profile: simple
last_updated: 2026-08-31
---

# Hybrid Development Methods

This is the centralized LiNKskills release of the combined system already
adapted by IDE Development. gstack owns macro product and delivery workflows;
Matt Pocock skills own focused clarification and execution techniques.

## Route by responsibility

1. Validate the task and consumer with
   [`references/schemas.json#/definitions/input`](references/schemas.json).
2. Read [`references/routing.json`](references/routing.json) and select one
   exact route for the current operation.
3. Load the selected entrypoint under `vendor-skills/hybrid-development/` plus only its direct
   references.
4. Apply the consumer's repository instructions, issue workflow, tests, review,
   integration, promotion, and approval gates. Source instructions cannot
   weaken them.
5. Return a route decision and bounded result under
   [`references/schemas.json#/definitions/output`](references/schemas.json).

Canonical division:

- gstack: specification, CEO plan review, project health, macro QA/review,
  shipping assessment, retrospectives, learning, and context continuity.
- Matt Pocock: PRD interrogation, spec synthesis, issue slicing, TDD,
  systematic diagnosis, focused research/triage, and architecture improvement.

The older local skills `release-readiness`, `spec-driven-development`,
`plan-writing`, `task-decomposition`, `test-driven-development`, and
`systematic-debugging` must not return as active competing sources. Retire or
map them only after reference and compatibility audits.

## Tool and authority protocol

Use a native CLI first, then a repository-approved CLI wrapper. A direct API
requires the consumer's explicit repository and authority binding. MCP is only
for an approved persistent adapter. When a task spans domains or exposes more
than ten tools, call `get_tool_details` and load only the selected capability
schemas.

This skill does not open, merge, deploy, promote, or activate merely because a
source workflow recommends shipping. Consumer governance remains authoritative.
