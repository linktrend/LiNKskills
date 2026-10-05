---
name: legal-privacy-reg-gap-analysis
description: "Prepare a draft privacy regulation gap analysis from authorized evidence, keeping scope and applicability conditional."
usage_trigger: "Prepare a draft privacy regulation gap analysis from authorized evidence, keeping scope and applicability conditional."
version: 0.1.1
release_tag: v0.1.1
created: 2026-10-04
author: LiNKskills Library
tags: [legal, compliance, task-specific, draft]
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
scope_out: ["No legal advice, final legal determination, certification, audit opinion, regulatory filing, signature, external communication or binding company decision.", "No invented law, facts, company policy, thresholds, dates, approvals, jurisdiction or evidence.", "No external effect, system mutation, notification, submission, publication, record closure, production or deletion.", "No source scripts, shell commands, APIs or connector aliases are callable task tools.", "No unnecessary sensitive, personal, confidential or privileged content in task state or output."]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-05
---
# Privacy Regulation Gap Analysis

## Role and purpose

Privacy Regulation Gap Analysis is a task-specific, evidence-grounded draft workflow for Sara's legal/corporate operations support. It enables the method in `advanced/advanced.md`; it does not grant legal authority, certify compliance, or establish company policy.

## Task boundary

Source applicability for the preserved reference is listed in `references/source-applicability.md`. Actual legal/standard applicability remains unresolved until current authoritative sources and company facts establish it. The pinned source is methodology provenance, not current law or a callable toolset.

## Substantive draft scope

The frontmatter “No legal advice” boundary prohibits a final authoritative legal opinion or binding legal determination; it does not prohibit evidence-based analysis and draft work expressly listed in this active procedure. Prepare substantive issue analysis, clauses, redlines, minutes, notices, policies, responses or options only within this task’s named inputs and output contract. Label drafts clearly, identify jurisdiction/source/date and unresolved facts, and leave consequential legal conclusions and binding actions to the authorized human or external counsel.

## Native tools and persistence

**Runtime persistence precedence.** The frontmatter `persistence.state_path` is portable template metadata, not an instruction to create a JSONL runtime file. In OpenClaw, checkpoint through the supported consumer-owned SQLite interface. Do not create `state.jsonl`, JSONL sidecars, or JSON runtime state. If the approved checkpoint interface is unavailable, keep the checkpoint reference in the named work product and disclose that limitation.


## Execution profile and checkpoint protocol

This is a heavy, resumable task profile. A **Specialist** handles one domain with at most ten tools; a **Generalist** spans domains or exceeds ten tools. The template's native CLI, CLI wrapper, direct API and MCP labels describe routing categories, not proof of a Sara interface. Use `get_tool_details` only when that exact native tool is available and current. The task contract names `state.jsonl` for resumability; persist checkpoints only through an authorized, supported consumer-owned route. If no such route is available, keep a draft checkpoint reference in the work product and disclose the limitation; do not create a local runtime sidecar.

This pack uses the Golden Template's CLI-first labels as routing categories: native CLI, CLI wrapper, direct API and MCP. They are not evidence that Sara has these executors. Current visible native tools and owner toolcards govern. No shell, source script, generic API alias or unverified connector is assumed. Use known authorized paths; draft-only writes require an explicit request. Checkpoints use the supported consumer-owner interface, not local JSONL runtime state.

Task-specific inputs and outputs are in `references/schemas.json#/definitions/input`, `/output` and `/state`. Active procedure: `advanced/advanced.md`. Source originals and file hashes: `references/upstream/SOURCE-MANIFEST.json`.
