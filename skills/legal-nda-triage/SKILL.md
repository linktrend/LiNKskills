---
name: legal-nda-triage
description: "Rapidly screen a supplied NDA for scope, term, confidentiality and embedded non-NDA obligations, producing a source-grounded issue shortlist and review route."
usage_trigger: "Use when Sara is asked to screen an incoming/outgoing NDA quickly, identify key review issues, or route it to a full NDA review."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, task-specific, sara, draft]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 32000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, list_dir, get_tool_details, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No unapproved legal commitments or external effects", "No invented facts, company positions, law, thresholds, or approval", "No source-system mutation or final legal authority"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# NDA Triage

## Specialist role
Prepare a substantive, evidence-led draft for Sara and the responsible human reviewer. Distinguish source facts, analysis, assumptions and open questions. Drafts may include legal interpretation/options where source-supported; final legal authority, signature, external communication, filing or live-system action is outside this skill.

## Purpose
Screen an NDA efficiently so the owner sees the material text issues and the next review step. This task does not replace a full clause-by-clause review. It never returns signature clearance.

## Sequence
1. Confirm document version, party roles, disclosure direction, purpose, transaction type and whether the text is a standalone NDA or embedded in a larger agreement.
2. Read any company-approved NDA positions supplied for this task. Record source/version. If absent or silent, mark company position `not_provided`/`silent`; do not use market-default thresholds.
3. Scan defined confidential information, permitted use and recipients, standard exceptions, compelled disclosure, care/security, duration/survival, return/destruction, residuals, remedies, governing law/forum and signatures/blank fields. Record section and concise text evidence for each material flag.
4. Search for hidden scope: standstill, exclusivity, non-solicit/non-compete, IP assignment/license, ROFR/MFN, broad arbitration, purchase/service commitments, personal-data/security terms. List these independently from confidentiality risks.
5. Compare text with supplied playbook. Give issue-specific rationale and business friction. Ask for only missing facts that change risk; do not stop assessment of separable clauses.
6. Route using descriptive, non-approval states: `limited_issues_for_owner_review`, `full_clause_review_recommended`, or `needs_context`. Explain why and identify reviewer. Never use GREEN to sign or auto-route to execution.

## Output
Document facts; scope classification; compact checklist table; high-priority issue list with clause reference/evidence/position status/rationale; missing attachments and facts; suggested next reviewer and questions. Detailed proposed clause text belongs to `legal-commercial-nda-review`.

## Boundary
Analyze substantive contract text as a draft. Do not sign, submit, send, update CLM, declare legally safe, or claim enforceability without jurisdiction/date/authority. A human makes final legal and commercial decisions.

## Native tools and persistence

The required tool names are abstract contract labels, not callable Lisa aliases. Map `read_file` to native `read` on a known authorized path; `write_file` to native `write`/`edit` only for the requested draft artifact; `get_tool_details` to inspection of the current native schema and owner toolcard. No callable `list_dir` exists. Use only approved read-only named Odoo/MCP tools if the currently visible schema supports the precise operation. If unavailable, use supplied evidence and report the interface gap. OpenClaw state remains SQLite-owned; checkpoints use the supported consumer owner interface, never local JSONL.

## Contract

Input/output/state: `references/schemas.json#/definitions/input`, `/output`, `/state`. Detailed task method: `advanced/advanced.md`. Exact upstream originals and licenses: `references/upstream/SOURCE-MANIFEST.json`.

## Execution profile and tooling levels

This is a Specialist workflow with a fixed native surface. The template's CLI-first labels are routing categories: Level 1 native CLI, Level 2 CLI wrapper, Level 3 direct API, Level 4 MCP. Lisa currently exposes no shell/CLI or direct API aliases, so do not invent commands. Use only current native tools whose schemas/toolcards are visible, including an approved read-only MCP where its exact contract allows the operation. If none is available, complete from supplied evidence and report the interface gap.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
