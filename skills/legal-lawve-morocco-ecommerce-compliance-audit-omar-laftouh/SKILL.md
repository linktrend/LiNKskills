---
name: legal-lawve-morocco-ecommerce-compliance-audit-omar-laftouh
description: "Audit a supplied Moroccan e-commerce website capture for privacy and consumer disclosure evidence, subject to current local-law verification."
usage_trigger: "Audit a supplied Moroccan e-commerce website capture for privacy and consumer disclosure evidence, subject to current local-law verification."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills adaptation
tags: [legal, task-specific, conditional, draft]
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
last_updated: 2026-10-05
---
# Moroccan E-commerce Site Compliance Evidence Audit

## Role and boundary

Audit a supplied Moroccan e-commerce website capture for privacy and consumer disclosure evidence, subject to current local-law verification. This task produces a draft work product, not a legal opinion, filing, signature, regulatory submission, external message, system mutation or company decision. Applicability is conditional on the supplied facts; never infer Sara’s role, client, entity, jurisdiction or authority from this source.

## Progressive disclosure

- Active workflow: [`advanced/advanced.md`](advanced/advanced.md)
- Typed task contracts and synthetic cases: [`references/schemas.json`](references/schemas.json) and [`references/eval-suite.json`](references/eval-suite.json)
- Exact copied source files, source commit, declarations and notices: [`references/upstream/SOURCE-MANIFEST.json`](references/upstream/SOURCE-MANIFEST.json) and [`references/source-copy-manifest.json`](references/source-copy-manifest.json)
- Source-specific adaptation: [`references/source-applicability.md`](references/source-applicability.md)

## Typed contracts and completion

Input contract: `references/schemas.json#/definitions/input`. Output contract: `references/schemas.json#/definitions/output`. Checkpoint metadata: `references/schemas.json#/definitions/state`. Synthetic cases: `references/eval-suite.json` and `references/task-contract-shape-fixture.json`. Structural validation does not establish task correctness or legal accuracy.

## Execution profile: Specialist

This heavy task uses the Specialist path. The Golden Template distinguishes native CLI, CLI wrapper, direct API, and MCP routing levels; those are categories, not evidence that an executor is available. Generalist/JIT discovery applies only if the actual task crosses domains or exceeds the supported tool surface. Inspect current native schemas and owner toolcards before use.

## Native interfaces and persistence

Abstract `read_file` maps to current native `read` on known, authorized paths. `write_file` maps to native `write`/`edit` only for the specifically requested draft artifact. `get_tool_details` means inspect the current native schema and owner toolcard; it is not a callable alias. `linkskills_use` and `linkbrain_read` are usable only if currently exposed for the requested read. Do not infer `list_dir`, shell, web, database, connector or business-system tools from source material.

The `lisa-openclaw` `state_path` is portable metadata only, never an instruction to create a sidecar. OpenClaw uses native agent SQLite checkpoints/history. If the consumer checkpoint interface is unavailable, state the limitation and continue useful work without inventing alternate persistence.

## Source and legal currency

Source bytes and notices are retained exactly as received. The source’s declared licenses, collection notice and any conflicts are reproduced in provenance; this pack makes no license-compliance or legal-clearance claim. Upstream legal assertions and dates are methodology material only. Before applying law, verify current primary authority for the actual jurisdiction and as-of date; otherwise mark the claim unverified.

## Completion

Deliver only this task’s output, with source pinpoints, status, missing facts, alternatives and accountable next questions. Routine internal drafts do not require blanket review; legal conclusions, external effects, filings, signatures and binding decisions remain with authorized owners. Keep `external_effects` and `mutations` empty.
