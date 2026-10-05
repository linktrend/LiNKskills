---
name: legal-practice-profile-customization
description: "Prepare a precise, source-linked change to one legal practice-profile setting without repeating the full bootstrap interview."
usage_trigger: "Use when the founder asks to change one existing legal profile section, practice position, escalation setting or output preference."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, practice-profile, task-specific]
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
scope_out: ["No assumed practice model, legal position, jurisdiction, integration, or authority", "No ~/.claude config writes or runtime sidecars", "No unapproved profile mutation"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Legal Practice Profile Customization

## Role
Prepare a founder-grounded legal profile draft. Keep facts, preferences, proposed positions, legal requirements and unknowns separate. No practice model or jurisdiction is inferred.

## Purpose
Handle a targeted profile change requested by the founder. Read current state and supporting material, identify the exact proposed field change and downstream effects, then return a reviewable before/after delta. Do not rerun the entire bootstrap interview for a single change.

## Workflow
1. Read the current authorized profile and source reference. Confirm the exact requested section/value, domain, owner and whether this is policy, preference, legal source or process.
2. Locate the corresponding domain card in `advanced/advanced.md`. Summarize current value and cite its source; if current value is absent or conflicting, show both and ask only the material question.
3. Draft a minimal before/after delta. Include rationale, affected workflows, reversibility, source date, open questions, and any profile sections that depend on the change. Leave unverified jurisdiction, authorities, thresholds, contacts or integrations blank.
4. Distinguish preference from legal obligation. For a legal rule, identify jurisdiction/date/current authority or state it remains unverified. For company position, require founder/owner evidence.
5. Return the exact proposed change, impact summary and owner confirmation. Do not write native config as part of review. If founder explicitly requests an internal artifact write, use only visible native write/edit and confirm readback.


## Native interface and state

`read_file` maps to native `read` on known paths; `write_file` maps to native `write`/`edit` only for an approved draft artifact; `get_tool_details` means inspect the current native schema and owner toolcard; `list_dir` is not callable. The four CLI-first levels are abstract routing labels only. Use no shell, integration probe or local config path. Checkpoint through the consumer owner interface; OpenClaw state remains SQLite-backed.

## Contract

See `references/schemas.json` and exact-source `references/upstream/SOURCE-MANIFEST.json`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

This Specialist workflow may be routed through native CLI, CLI wrapper, direct API, or MCP only when that exact operation is in the current native tool schema and owner toolcard.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
