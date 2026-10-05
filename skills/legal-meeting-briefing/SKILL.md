---
name: legal-meeting-briefing
description: "Prepare evidence-linked briefings and action capture for meetings with legal, contract, compliance or governance relevance."
usage_trigger: "Use when Sara is asked to prepare a pre-read, agenda, questions, negotiation brief or follow-up action register for a legal-relevant meeting."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-04
author: LiNKskills Library
tags: [legal, task-specific, sara, draft]
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
scope_out: ["No unapproved legal commitments or external effects", "No invented facts, company positions, law, thresholds, or approval", "No source-system mutation or final legal authority"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-04
---
# Legal Meeting Briefing

## Specialist role
Prepare a substantive, evidence-led draft for Sara and the responsible human reviewer. Distinguish source facts, analysis, assumptions and open questions. Drafts may include legal interpretation/options where source-supported; final legal authority, signature, external communication, filing or live-system action is outside this skill.

## Purpose
Prepare a concise, decision-oriented briefing for a meeting with legal relevance and capture resulting actions from supplied notes. Use evidence available through authorized native interfaces. Do not assume access to private calendars, messages, matter files or contract systems.

## Sequence
1. Confirm meeting date/duration, purpose/type, participants and roles, agenda, Sara's role (preparer/participant/advisor/observer), intended audience and preparation time. Ask only for missing facts that change scope; otherwise mark assumption.
2. Gather only authorized, task-relevant records: prior decision/action notes, supplied contracts, compliance status, business context, deadlines and approved playbook positions. Attach source title/version/date/section. Preserve conflicts rather than resolving by recency alone.
3. Identify meeting objective, decisions required, factual background, current position, open issues, participant interests supported by evidence, preparation gaps and questions. Draft proposed options or contract/resolution language when requested; mark as draft and cite basis.
4. Tailor sections to meeting type: contract negotiation (issues and fallback); board/committee (decision and resolutions draft); compliance review (obligations/status/evidence); vendor/customer (open contract/service questions); regulator/counsel (facts, correspondence and precise questions). Do not include irrelevant sections.
5. Produce the briefing and timeboxed agenda. After meeting notes are supplied, convert decisions into action items with owner, due date, dependencies and evidence of completion; leave unknown owner/date blank and identify them.
6. Provide audience-specific handling. Do not label privilege or confidentiality unless a company-approved rule is supplied. Do not send invites, contact participants, update a matter system or circulate the brief.

## Output
Meeting facts and source date; objective; concise background; status/decisions; prioritized agenda; participant roles grounded in supplied context; questions and decision options; preparation gaps; action table (action, owner, due, dependency, status); follow-up brief. Substantive legal analysis and drafts are permitted with citations and explicit unresolved jurisdiction/source issues; final legal positions/actions remain with the owner.

## Native tools and persistence

The required tool names are abstract contract labels, not callable Lisa aliases. Map `read_file` to native `read` on a known authorized path; `write_file` to native `write`/`edit` only for the requested draft artifact; `get_tool_details` to inspection of the current native schema and owner toolcard. No callable `list_dir` exists. Use only approved read-only named Odoo/MCP tools if the currently visible schema supports the precise operation. If unavailable, use supplied evidence and report the interface gap. OpenClaw state remains SQLite-owned; checkpoints use the supported consumer owner interface, never local JSONL.

## Contract

Input/output/state: `references/schemas.json#/definitions/input`, `/output`, `/state`. Detailed task method: `advanced/advanced.md`. Exact upstream originals and licenses: `references/upstream/SOURCE-MANIFEST.json`.

## Execution profile and tooling levels

This is a Specialist workflow with a fixed native surface. The template's CLI-first labels are routing categories: Level 1 native CLI, Level 2 CLI wrapper, Level 3 direct API, Level 4 MCP. Lisa currently exposes no shell/CLI or direct API aliases, so do not invent commands. Use only current native tools whose schemas/toolcards are visible, including an approved read-only MCP where its exact contract allows the operation. If none is available, complete from supplied evidence and report the interface gap.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
