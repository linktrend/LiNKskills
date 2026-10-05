---
name: general-contract-risk-analysis
description: "Analyze an agreement for material risks, key terms, document gaps and internal inconsistencies without applying an organization-specific playbook."
usage_trigger: "Analyze an agreement for material risks, key terms, document gaps and internal inconsistencies without applying an organization-specific playbook."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, contracts, task-specific]
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
scope_out: ["No signature, communication, CLM write, or binding action", "No invented playbook position, current law, benchmark or risk threshold"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# General Contract Risk Analysis

## Role

Prepare a substantive, evidence-linked contract risk review and clearly label draft legal analysis, factual assumptions, and missing authority.

## Workflow

Use `advanced/advanced.md` for the full workflow and focused cards: `advanced/cards/five-clause-initial-screen.md` and `advanced/cards/technology-contract-checklist.md`. Read the entire agreement and available playbook/context before conclusions. Draft clause-specific analysis and optional redline language as an internal review artifact. Escalate consequential legal conclusions and external actions to the named reviewer.

## Native interface mapping

Abstract `read_file` maps to native `read` on known authorized paths; `write_file` maps to native `write`/`edit` only for the specifically approved draft artifact; `get_tool_details` means inspect the current native tool schema and owner toolcard; `list_dir` is not callable. Native CLI, CLI wrapper, direct API, or MCP is usable only when the exact interface is present in the current native schema. If absent, work from supplied records and name the capability gap; do not invent a callable alias. No shell scripts or source-system mutation. OpenClaw runtime state remains SQLite; checkpoints use the supported consumer owner interface.

## Contract

The frontmatter `state.jsonl` path is portable Golden Template metadata only.
In OpenClaw, retained sessions and checkpoints remain SQLite-owned. Do not
create JSONL state sidecars or write private histories or runtime logs.

Input: `references/schemas.json#/definitions/input`; output: `references/schemas.json#/definitions/output`; state: `references/schemas.json#/definitions/state`. Task methods: `advanced/advanced.md`. Exact originals/provenance: `references/upstream/SOURCE-MANIFEST.json`; source-to-method decisions: `references/source-selection.md`.

This is a Specialist workflow, not a blanket refusal: prepare substantive draft analysis, clause alternatives, and negotiation options within assigned scope; never sign, send, or claim binding approval.
