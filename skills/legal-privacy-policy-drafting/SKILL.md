---
name: legal-privacy-policy-drafting
description: "Draft or revise a jurisdiction-aware privacy policy for a specified website, application or service from confirmed processing facts and current authoritative sources."
usage_trigger: "Draft or revise a jurisdiction-aware privacy policy for a specified website, application or service from confirmed processing facts and current authoritative sources."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, privacy, task-specific, draft]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file, get_tool_details, linkskills_use, linkbrain_read]
dependencies: []
permissions: [fs_read, fs_write]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Privacy Policy Drafting

## Role and outcome

Draft or revise a jurisdiction-aware privacy policy for a specified website, application or service from confirmed processing facts and current authoritative sources. Return a draft with visible unknowns, a confirmed-practices-to-clauses reconciliation, current-source citations, and counsel/founder review points. A policy contains representations about actual practices: do not invent company facts or legal compliance.

## Progressive disclosure

- Active procedure: [`advanced/advanced.md`](advanced/advanced.md)
- Typed contracts: [`references/schemas.json`](references/schemas.json#/definitions/input), [`references/schemas.json`](references/schemas.json#/definitions/output), [`references/schemas.json`](references/schemas.json#/definitions/state)
- Task-shaped synthetic inputs: [`references/task-contract-shape-fixture.json`](references/task-contract-shape-fixture.json)
- Complete source copies/notices: [`references/upstream/SOURCE-MANIFEST.json`](references/upstream/SOURCE-MANIFEST.json)

## Native tools and checkpoint

This is a Specialist task. The Golden Template distinguishes Native CLI, CLI wrapper, Direct API and MCP; those are routing levels, not assumed capabilities. Use current visible native `read` on known approved source paths and `write`/`edit` only for the requested internal draft. `get_tool_details` means inspect current native schemas and owner toolcards. Do not invent external legal-data-hunter, cite-guard, file conversion, or publishing tools.

For `lisa-openclaw`, the `state_path` is a portable declaration only, never an instruction to create a JSONL sidecar. Use the native agent SQLite checkpoint/history. If that consumer boundary is unavailable, report it instead of inventing alternate persistence.

## Boundaries

The draft may be prepared before every fact is known, with visible `[GAP]` markers. Do not publish, send, sign, change system records, claim compliance, or present a draft as legal advice. Obtain founder confirmation for company practices and counsel review for high-risk or legal interpretation before publication.
