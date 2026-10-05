---
name: legal-practice-bootstrap-interview
description: "Run a founder-led, evidence-based bootstrap interview to establish a legal practice/company profile from seed documents and domain needs."
usage_trigger: "Use when a legal practice profile is missing, contains placeholders, or the founder asks to establish or refresh the initial practice setup."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, practice-profile, task-specific]
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
scope_out: ["No assumed practice model, legal position, jurisdiction, integration, or authority", "No ~/.claude config writes or runtime sidecars", "No unapproved profile mutation"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Legal Practice Bootstrap Interview

## Role
Prepare a founder-grounded legal profile draft. Keep facts, preferences, proposed positions, legal requirements and unknowns separate. No practice model or jurisdiction is inferred.

## Purpose
Guide a founder through initial legal practice setup, prefill known facts from authorized records, ask adaptive questions about missing company/practice facts, and produce a reviewable profile draft plus source and decision register. Do not assume in-house vs private practice or infer connected systems.

## Workflow
1. Read the authorized profile/reference index first. Prefill facts with source, date and confidence; do not repeat answered questions or treat a draft as canon.
2. Confirm operating model (in-house, external practice, both, undecided), scope of services and role/audience. If unknown, ask the founder; leave uncertain rather than activating a module.
3. Select relevant domain modules from `advanced/advanced.md`; run a quick or full interview based on founder preference and task complexity. Ask short rounds and explain why each material fact changes workflow or risk.
4. For each module, review only supplied seed documents, capture title/version/date/owner, extract positions carefully, preserve conflicting excerpts, and identify missing source documents. Distinguish policy, preferred position, legal rule and proposed change.
5. Ask about role-specific procedures, escalation triggers, output style, reviewer/decision owner, authority limits and supported tools. Do not claim a connector is available unless its current schema allows a real read.
6. Deliver profile draft, fact/source ledger, module selection, unresolved decisions, conflicts, reviewer and acceptance questions. Do not write plugin config or probe integrations. A user-requested write is allowed only to an approved draft artifact through the visible native interface.
7. Before a later implementation, the profile owner reviews the exact diff and confirms. If no owner interface exists, report a capability gap.


## Native interface and state

`read_file` maps to native `read` on known paths; `write_file` maps to native `write`/`edit` only for an approved draft artifact; `get_tool_details` means inspect the current native schema and owner toolcard; `list_dir` is not callable. The four CLI-first levels are abstract routing labels only. Use no shell, integration probe or local config path. Checkpoint through the consumer owner interface; OpenClaw state remains SQLite-backed.

## Contract

See `references/schemas.json` and exact-source `references/upstream/SOURCE-MANIFEST.json`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

This Specialist workflow may be routed through native CLI, CLI wrapper, direct API, or MCP only when that exact operation is in the current native tool schema and owner toolcard.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
