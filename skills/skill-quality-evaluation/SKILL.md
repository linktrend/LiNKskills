---
name: skill-quality-evaluation
description: "Evaluate a pinned skill release against frozen task cases, trigger behavior, typed output assertions and regression criteria; deliver bounded evidence and revision recommendations."
usage_trigger: "Evaluate a pinned skill release using frozen cases and supplied or owner-authorized evaluation evidence."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [skill-quality, evaluation, catalog-quality, draft]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No skill authoring or structural migration", "No qualification, admission, publication or activation", "No paid model calls or new evaluation services"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Skill Quality Evaluation

## Role and outcome

Evaluate the intended behavior of a pinned skill release and produce a bounded evidence packet with case results and revision recommendations. Owner: LiNKskills Librarian / Skill Library quality process; this is not Sara-bound. It remains draft and uncertified; no semantic evaluation or qualification is claimed by its creation.

## Progressive disclosure

- Active method: [`advanced/advanced.md`](advanced/advanced.md)
- Input/output/state contracts: [`references/schemas.json`](references/schemas.json)
- Evaluation assertions: [`references/eval-suite.json`](references/eval-suite.json) and YAML mirror
- Complete pinned source tree/notices: [`references/upstream/SOURCE-MANIFEST.json`](references/upstream/SOURCE-MANIFEST.json)

## Workflow

1. Pin immutable candidate, intended user task, trigger and contracts.
2. Freeze a balanced suite before scoring.
3. Inspect only supplied or explicitly owner-authorized evidence.
4. Separate deterministic assertions from qualitative review and report denominators.
5. Propose evidence-linked, testable improvements.
6. Report `no_claim`, `hold`, or `candidate_for_independent_review`; never claim qualification.

## Native interfaces

`read_file` maps to native `read`; `write_file` maps to native `write`/`edit` for an explicitly requested internal evaluation plan/report. `get_tool_details` means inspect current native schemas and owner toolcards; there is no callable alias. Do not execute source scripts, use source viewer HTML, use a paid service, or write a catalog/provider system. Consumer runtime state remains SQLite/native-owner controlled.

## Contracts

- Input: `references/schemas.json#/definitions/input`
- Output: `references/schemas.json#/definitions/output`
- State: `references/schemas.json#/definitions/state`
- Source map and notices: `references/upstream/SOURCE-MANIFEST.json`

## Tool levels and profile

This is a Specialist workflow. Native CLI and CLI wrapper are abstract routing categories; no shell executor is assumed. Direct API and MCP access are permitted only where the current native schema and owner toolcard expose an exact authorized read interface. No such interface is required for this draft.
