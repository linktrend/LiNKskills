---
name: legal-matter-context-management
description: "Manage scoped legal matter context through supported owner interfaces: intake, list, select, archive/close, or detach from an active matter."
usage_trigger: "Use when Sara needs a legal matter context created, listed, selected, closed, or detached, or a legal workflow needs an explicit matter scope."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, matter-context, privacy, task-specific]
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
scope_out: ["No assumption of in-house/private-practice model", "No Claude profile/filesystem commands or custom runtime stores", "No access to other matters without explicit authorized scope"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Legal Matter Context Management

## Purpose

Keep each authorized legal engagement’s facts, people and work product within an explicit scope. Support matter intake, list, select, close/archive and detach operations only through current consumer-owned context/session/artifact interfaces. This pack cannot create a new matter-store implementation or modify native runtime configuration.

## Operating-model intake

Before a first matter operation, establish the founder-confirmed operating model (in-house, external multi-client practice, both, or undecided), the company’s approved matter-context interface, authorized users and data boundary. Record exact evidence/date. Unknown stays `unknown`; do not configure private practice or in-house defaults. Ask the founder only for consequential missing facts.

## Workflow

1. Read the authorized task scope and known matter index through the native owner interface if available. Do not enumerate private files or search hidden profile locations.
2. Choose one operation: `new`, `list`, `switch`, `close`, or `detach`. Validate operation against the visible consumer tool schema and owner toolcard. If not exposed, prepare a draft packet and report the interface gap; do not invent an invocation.
3. For `new`, confirm unique matter identity and intake the minimum fields: name/slug, client/counterparty, matter type/domain, purpose, parties and roles, owner, status, known jurisdiction (evidence only), sensitive-data category, retention/closure owner, and related-matter references. Apply the domain card in `advanced/advanced.md`. Never assume law-firm/in-house mode.
4. For `list`, return only authorized matter IDs, neutral descriptions, status and active flag. Avoid leaking substance into a broad list.
5. For `switch`, verify user scope and exact matter ID, then bind subsequent work to that context using the supported consumer selector. Confirm the selected ID back; do not carry forward prior-matter notes.
6. For `close`, record requested close status and prepare archive/retention disposition. Invoke the existing owner interface only if explicitly authorized and the current schema supports it; never delete records by default.
7. For `detach`, stop matter-specific context and return to practice/company-level context without opening, merging, or summarizing matter content.
8. Keep unrelated matters isolated. A cross-matter comparison needs explicit scope, authorized references and a reason; include only the minimum necessary excerpts.
9. Validate result, open questions and isolation boundary. Use consumer-owned checkpoints only; native OpenClaw state remains SQLite-backed.

## Domain cards

See `advanced/advanced.md` for the nine source-specific intake variants: AI governance, commercial, corporate, employment, IP, litigation, privacy, product and regulatory. They share the same context-management job but retain distinct fact prompts and applicability. Their substantive legal work stays in its own task-specific skill.

## Contract

Input/output/state: `references/schemas.json#/definitions/input`, `/output`, `/state`. Full exact source entries are copied under `references/upstream/` and indexed by `SOURCE-MANIFEST.json`.

## Execution profile and tooling levels

This is a Specialist workflow. CLI-first labels are abstract routing categories: Level 1 native CLI, Level 2 CLI wrapper, Level 3 direct API, Level 4 MCP. Sara’s current surface has no shell/CLI or callable aliases; use only currently visible native schemas and supported owner interfaces. If the context manager is not exposed, draft the operation and report the precise gap. Do not construct a runtime substitute.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
