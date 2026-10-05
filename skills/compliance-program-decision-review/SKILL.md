---
name: compliance-program-decision-review
description: "Prepare an evidence-grounded review packet for an authorized decision owner about compliance-framework commitment, the annual audit calendar, evidence consolidation, mock-audit results, or management-review decisions."
usage_trigger: "Use before committing to a new framework, finalizing an annual audit calendar, a compliance-program management review, or a certification-stage-1 decision review; route named-milestone readiness sequencing to compliance-framework-compliance-readiness and standing program architecture to compliance-framework-compliance-os."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library
tags: [compliance, decision-review, task-specific, draft]
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
scope_out: ["No final legal or applicability determination, certification, audit opinion, or declaration that a program is compliant or ready without the required counsel, specialist, and owner review.", "This review does not choose or commit to a framework, calendar, control, evidence standard, budget, certification, or company policy. Report a prior decision only when the authorized owner or explicitly delegated role is established by supplied evidence; preserve decisions reserved to Carlos.", "Do not invent law, company facts, thresholds, dates, audit results, approvals, jurisdiction, or source evidence.", "No external effects, official record changes, filings, signatures, notifications, publication, or system mutations.", "Preserved upstream scripts and APIs are provenance only; they are not callable task tools.", "Do not put unnecessary personal, confidential, or privileged content in task state or output."]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-05
---
# Compliance Program Decision Review

## Role and purpose

Prepare a draft decision-review packet from authorized program records. The packet pressure-tests six recurring decisions and identifies evidence, trade-offs, owners, unknowns, and exact questions for the decision owner. Sara may perform the review under her assigned operations role. A decision is recorded only when supported by the authorized decision owner’s supplied evidence or explicit delegated authority. Preserve decisions reserved to Carlos; do not assume delegation or make an unassigned commitment, legal determination, policy choice, certification, or approval.

## Task boundary and routing

Use this skill to review a framework commitment, annual audit-calendar decision, cross-framework evidence-consolidation proposal, mock-audit record, management-review decision, or a certification-stage-1 sign-off request. It does not make the decision or assert compliance.

- A named audit window, milestone, or new-framework launch requiring gap sequencing routes to `compliance-framework-compliance-readiness`.
- Standing framework portfolio, control/evidence architecture, recurring program backlog, or annual calendar design routes to `compliance-framework-compliance-os`.
- This skill reviews a proposed annual calendar and prepares decision options; it does not design or adopt the calendar.
- Framework-specific legal or technical analysis routes to the applicable specialist; preserve that specialist’s result as an input, not as an assumed fact.

## Inputs and outputs

Use `references/schemas.json#/definitions/input` and `/output`. Inputs may say `unknown` where facts have not been confirmed. Complete separable review work; never fill an unknown with an assumption. Return a six-question decision-review packet with evidence references and owner actions, or `needs_context` with exact missing inputs, unknown facts, and partial work.

## Tooling protocol

Use a suitable **native CLI** when it is actually available; otherwise use a verified **CLI wrapper**. A **direct API** is an exception that requires an exact visible interface and a documented need. Use **MCP** only for a persistent session-based service. These categories describe routing order, not proof that Sara has a particular executor.

## Native tools and persistence

The Golden Template's CLI/API/MCP labels are routing categories, not proof that Sara has those interfaces. The frontmatter tool names are contract metadata: map `read_file` to an actually visible native read, and `write_file` to an actually visible native write/edit for an authorized internal draft. Do not assume `list_dir` or `get_tool_details` is available; inspect paths through visible native reads and use tool-detail lookup only if the native tool exists. Read supplied records; do not execute preserved upstream scripts. Write only a requested internal draft to an authorized location. Checkpoints use the supported consumer-owned SQLite interface when available; never create local JSONL or other runtime sidecars. If no approved checkpoint interface is available, include the checkpoint limitation in the work product.

## Execution profile

This is a heavy, resumable review task. A Specialist handles one compliance domain with at most ten tools; a Generalist spans domains or uses more than ten tools. Use `get_tool_details` only if that exact native tool is currently available and the task needs its schema. Do not invent tool aliases.

## Completion criteria

Return `completed_draft` only when the six assessments, review summary, options, and owner decision questions contain task-specific content grounded in supplied evidence. Cite exact supplied sources. If decisive evidence or authority is missing, return `needs_context` or `escalate`; identify the missing source and owner and finish independent review portions. External effects and mutations must remain empty.

## Progressive disclosure

- Procedure: [`advanced/advanced.md`](advanced/advanced.md)
- Contracts and typed examples: [`references/schemas.json`](references/schemas.json), [`references/task-contract-shape-fixture.json`](references/task-contract-shape-fixture.json), and [`examples/valid-input.json`](examples/valid-input.json), [`examples/valid-output.json`](examples/valid-output.json), [`examples/needs-context-output.json`](examples/needs-context-output.json), [`examples/invalid-duplicate-question-id.json`](examples/invalid-duplicate-question-id.json)
- Evaluation cases: [`references/eval-suite.json`](references/eval-suite.json)
- Source scope and preserved originals: [`references/source-applicability.md`](references/source-applicability.md) and [`references/upstream/SOURCE-MANIFEST.json`](references/upstream/SOURCE-MANIFEST.json)
- Current interface limits: [`references/api-specs.md`](references/api-specs.md)
