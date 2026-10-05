---
name: legal-lawve-collaboration-platform-advisor-scott-margetts
description: "Design or improve legal-matter collaboration workspace architecture, workflow brief, dashboard or adoption/data-quality plan."
usage_trigger: "Design or improve legal-matter collaboration workspace architecture, workflow brief, dashboard or adoption/data-quality plan."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, task-specific, draft, conditional]
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
# Legal Collaboration Platform Advisor

## Role and outcome

Design or improve legal-matter collaboration workspace architecture, workflow brief, dashboard or adoption/data-quality plan. The deliverable is a structured draft with source trace, scope/applicability, uncertainties and next steps. The pack is conditional where its source method is tied to a specific jurisdiction, framework, sector, client or education context; never infer that condition from Sara’s role or company facts.

## Progressive disclosure

- Active task method: [`advanced/advanced.md`](advanced/advanced.md)
- Typed contracts and task-shaped cases: [`references/schemas.json`](references/schemas.json), [`references/eval-suite.json`](references/eval-suite.json), [`references/task-contract-shape-fixture.json`](references/task-contract-shape-fixture.json)
- Complete pinned source subtree and notices: [`references/upstream/SOURCE-MANIFEST.json`](references/upstream/SOURCE-MANIFEST.json)
- Source-specific applicability and adaptation notes: [`references/source-applicability.md`](references/source-applicability.md)

## Contract and completion

Inputs, outputs and resumable state are defined in `references/schemas.json#/definitions/input`, `references/schemas.json#/definitions/output`, and `references/schemas.json#/definitions/state`. Finish only this task’s distinct deliverable; cite source/date/pinpoint for material facts; separate verified evidence, reported fact, inference, proposal and unknown. Keep `external_effects` and `mutations` empty. This is a draft, uncertified pack: schema validation does not prove task correctness, legal accuracy, law applicability, runtime behavior, admission or qualification.

## Tooling and persistence

This is a Specialist workflow with a small fixed tool surface; it does not become Generalist merely because the subject mentions several statutes. The Golden Template distinguishes Native CLI, CLI wrapper, Direct API, and MCP routing levels; those labels do not imply those surfaces are available here. Read only known approved paths through native `read`; write only the requested internal draft through native `write`/`edit`. `get_tool_details` means inspect the current visible native schema and owner toolcard, not invoke a callable alias. `linkskills_use` and `linkbrain_read` are usable only when the current schema exposes them for this purpose. There is no assumed `list_dir`, shell, external legal database, business-system connector or third-party source MCP.

For the `lisa-openclaw` consumer, frontmatter `state_path` is a portable declaration only, never an instruction to create a JSONL sidecar. OpenClaw’s native agent SQLite checkpoint/history is authoritative. Resume through the consumer-provided native session boundary; if unavailable, state the missing continuation capability and keep the response useful without inventing alternate storage.

## Authority boundary

Drafts, analysis, source research planning and reversible internal artifacts are allowed within this task. Do not sign, file, send, configure a legal/business system, change records, make a personnel or policy decision, claim compliance, or represent the draft as approved. Read access to an explicitly authorized source is allowed; write access is limited to the requested internal artifact. Current law and regulatory requirements must be checked against authoritative primary materials at task time; this copied source is methodology evidence, not law or company fact.
