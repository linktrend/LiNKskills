---
name: legal-ip-invention-intake
description: "Capture a confidential invention disclosure with inventors/contributors, conception/reduction dates, problem/solution, alternatives, prior disclosures/publications, funding/third-party materials, assignments and countries. Prepare a task-specific, evidence-linked draft and identi"
usage_trigger: "Capture a confidential invention disclosure with inventors/contributors, conception/reduction dates, problem/solution, alternatives, prior disclosures/publications, funding/third-party materials, assignments and countries."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, task-specific, draft, ip_legal]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file, get_tool_details, list_dir, linkskills_use, linkbrain_read]
dependencies: []
permissions: [fs_read, fs_write]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Legal Ip Invention Intake

## Role and outcome

Prepare the task-specific deliverable for **invention disclosure summary, inventor/contribution matrix, disclosure timeline, third-party/assignment flags and patent counsel intake questions**. Active method: [`advanced/advanced.md`](advanced/advanced.md). Output is a reviewable draft or evidence-based analysis with provenance and uncertainty; it is not an approval, filing, signature, legal commitment, or external action. Sara may complete substantive analysis and draft language within the stated scope. Carlos or external counsel reviews consequential legal conclusions/actions and final commitments.

## Progressive disclosure

- Active procedure: [`advanced/advanced.md`](advanced/advanced.md)
- Typed contracts and synthetic tests: [`references/schemas.json`](references/schemas.json), [`references/eval-suite.json`](references/eval-suite.json)
- Complete pinned source content and notices: [`references/upstream/SOURCE-MANIFEST.json`](references/upstream/SOURCE-MANIFEST.json)
- Source applicability: [`references/source-applicability.md`](references/source-applicability.md)

## Contract and completion

Input, output and state contracts are defined in `references/schemas.json`. Complete this task’s distinct output, show source/date/jurisdiction applicability, identify uncertainties, and leave `external_effects` and `mutations` empty. See the active procedure for the available native-interface mapping and authority boundary. This pack is **draft and uncertified**; structural validation does not establish semantic quality, legal correctness, admission, qualification, or consumer activation.


## Tooling and contracts

This is a **Specialist** workflow with a small fixed tool surface. The Golden Template distinguishes **Native CLI**, **CLI wrapper**, **Direct API**, and **MCP** routing levels; these labels do not imply tools are available to Sara. Use only the current visible native tool schemas and owner toolcards.

- `read_file` maps to native `read` for known approved paths.
- `write_file` maps to native `write`/`edit` only for an explicitly requested internal draft.
- `get_tool_details` means inspect the current visible native schema and owner toolcard; it is not a callable alias. `list_dir` is not available.
- `linkskills_use`, `linkbrain_read`, and named read-only Odoo/MCP tools may be used only if the current native schema exposes that exact interface and operation.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`. Detailed task method: `advanced/advanced.md`. Persistent OpenClaw runtime state stays in SQLite; never substitute skill-local JSONL state. Use a checkpoint interface only when the consumer owner provides it.


## Tooling and contracts

This is a **Specialist** workflow with a small fixed tool surface. The Golden Template distinguishes **Native CLI**, **CLI wrapper**, **Direct API**, and **MCP** routing levels; these labels do not imply tools are available to Sara. Use only the current visible native tool schemas and owner toolcards.

- `read_file` maps to native `read` for known approved paths.
- `write_file` maps to native `write`/`edit` only for an explicitly requested internal draft.
- `get_tool_details` means inspect the current visible native schema and owner toolcard; it is not a callable alias. `list_dir` is not available.
- `linkskills_use`, `linkbrain_read`, and named read-only Odoo/MCP tools may be used only if the current native schema exposes that exact interface and operation.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`. Detailed task method: `advanced/advanced.md`. Persistent OpenClaw runtime state stays in SQLite; never substitute skill-local JSONL state. Use a checkpoint interface only when the consumer owner provides it.

## OpenClaw checkpoint interpretation

For the `lisa-openclaw` consumer, the frontmatter `state_path` is a portable validation/checkpoint declaration only; it is not a runtime file-write instruction. The native agent-scoped SQLite session is the sole authoritative checkpoint. Record the task ID, exact skill release, current phase, established facts, source/artifact references, unresolved inputs and next action in the ordinary native response. Resume the same retained session through its native history/status interface. Never create `.workdir/tasks/*/state.jsonl` or a parallel checkpoint ledger. If the native retained-session boundary cannot honor continuation, report HOLD and the missing capability; do not invent an adapter or silently switch persistence.
