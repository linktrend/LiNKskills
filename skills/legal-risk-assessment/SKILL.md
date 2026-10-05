---
name: legal-risk-assessment
description: "Prepare an evidence-based legal risk memo or register entry with explicit severity, likelihood, mitigations, residual uncertainty and owner actions."
usage_trigger: "Use when Sara is asked to assess, document, compare or monitor a legal/compliance exposure or prepare a risk-register update."
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
# Legal Risk Assessment

## Specialist role
Prepare a substantive, evidence-led draft for Sara and the responsible human reviewer. Distinguish source facts, analysis, assumptions and open questions. Drafts may include legal interpretation/options where source-supported; final legal authority, signature, external communication, filing or live-system action is outside this skill.

## Purpose
Document and reason about a defined legal/compliance exposure so the accountable owner can choose mitigation and review. Use a supplied organizational risk rubric where one exists. The assessment is a draft, not legal authority or a verified probability forecast.

## Sequence
1. Define the event, affected objective/population, time horizon, trigger, known facts and source dates. Distinguish observed facts from hypotheses.
2. Identify the governing text, contract clause, rule or obligation actually at issue. State jurisdiction and as-of date only when provided or verified from a current authoritative source. If absent, analyze the operational scenario and mark law-dependent fields unresolved.
   When a conclusion depends on case law, retrieve current primary authorities for the actual jurisdiction and search for contrary, narrowed or overruled decisions, not only supporting cases. Use recent commentary as a discovery aid and verify its propositions against primary text. Record decision dates, subsequent treatment, conflicting authority and verification gaps before rating risk; age alone neither invalidates nor proves a rule. Cite verified authorities inline with source/date and distinguish unsupported recollection. GoodLegal/French/EU examples in the copied variant apply only if the matter and currently granted tool support them; do not invent those tools or universal age thresholds.

3. Identify plausible causes, current controls and evidence they operate; assess potential impact across legal, financial, operational, privacy, safety and reputation dimensions relevant to the case. Do not manufacture monetary bands.
4. Assess likelihood only against supplied event data, exposure frequency, control evidence and time horizon. If evidence is inadequate, state `not rated` and list what would support a rating.
5. Apply company-approved severity/likelihood scale only when supplied, with scale version and rationale. Otherwise give qualitative ranges and explicitly say uncalibrated; do not apply upstream 5x5 score thresholds, green/red labels or mandatory-counsel triggers as universal policy.
6. Develop options: avoid, reduce, transfer/share, accept/monitor. For each, state effect, owner, cost/dependency, residual exposure and whether external counsel/professional input is needed. Present the strongest alternative explanation and prevent mitigations from being mistaken for proof.
7. Produce a memo or register entry with owner, review date, trigger, evidence, unresolved facts, next steps and reviewer. Do not declare the issue closed or change a live register without explicit authorization.

## Output
Risk statement; context and source table; consequence and likelihood basis; existing-control evidence; uncertainty/conflicting facts; approved scale/rating or `unrated`; mitigation alternatives; residual risk; monitoring indicators/owner/date; specific counsel or decision questions.

## Native tools and persistence

The required tool names are abstract contract labels, not callable Lisa aliases. Map `read_file` to native `read` on a known authorized path; `write_file` to native `write`/`edit` only for the requested draft artifact; `get_tool_details` to inspection of the current native schema and owner toolcard. No callable `list_dir` exists. Use only approved read-only named Odoo/MCP tools if the currently visible schema supports the precise operation. If unavailable, use supplied evidence and report the interface gap. OpenClaw state remains SQLite-owned; checkpoints use the supported consumer owner interface, never local JSONL.

## Contract

Input/output/state: `references/schemas.json#/definitions/input`, `/output`, `/state`. Detailed task method: `advanced/advanced.md`. Exact upstream originals and licenses: `references/upstream/SOURCE-MANIFEST.json`.

## Execution profile and tooling levels

This is a Specialist workflow with a fixed native surface. The template's CLI-first labels are routing categories: Level 1 native CLI, Level 2 CLI wrapper, Level 3 direct API, Level 4 MCP. Lisa currently exposes no shell/CLI or direct API aliases, so do not invent commands. Use only current native tools whose schemas/toolcards are visible, including an approved read-only MCP where its exact contract allows the operation. If none is available, complete from supplied evidence and report the interface gap.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.

Input contract: `references/schemas.json#/definitions/input`; output contract: `references/schemas.json#/definitions/output`; state contract: `references/schemas.json#/definitions/state`.
