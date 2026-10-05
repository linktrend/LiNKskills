---
name: company-incident-continuity
description: "An evidence-bounded method for prospective risk registers and incident and continuity coordination, keeping prospective risk review separate from live response."
usage_trigger: "Use for synthetic, redacted, or public operational-risk or incident evidence when an owner needs a prospective risk register, outage/security/continuity review, or recovery and closure proposal without control activation, deployment, communication, credential, or authority mutation."
version: 1.0.1
release_tag: v1.0.1
created: 2026-08-25
author: LiNKskills Library
tags: [incident, outage, security, continuity, recovery, evidence]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5.6-luna
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [governed-browser-use, executive-decisions-governance]
permissions: [fs_read, fs_write]
scope_out: ["Do not deploy, roll back, isolate, rotate credentials, or mutate infrastructure", "Do not send internal or customer communication or claim that it was sent", "Do not approve recovery, continuity, security, Program Ledger, or deployment actions", "Do not expose credentials, private incident records, customer data, or confidential company material in releases, fixtures, telemetry, or state"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-06
---

# Company Incident and Continuity Management

This skill prepares an evidence-bound coordination artifact for an outage,
security incident, continuity concern, or recovery review. It is not an
incident commander, deployment controller, security authority, customer
messaging service, backup system, Program Ledger, or durable incident store.

## Prospective risk-register contract

Route `mode=prospective_risk_register` to its own input/output schema and helper branch. This is a prospective inventory and treatment proposal, not incident response. Do not manufacture `incident_ref`, incident type, severity, active state, or closure fields. Each risk preserves the supplied `evidence_refs` for its cause, event, consequence, likelihood/impact statement, current-control evidence, and residual statement. Use only an owner-supplied scale and tolerance. A caller advisory, and an owner assessment without an evidenced scale, must state `Unknown:` followed by a nonempty reason for inherent rating; only an owner with an evidenced scale may supply `Rating: <label>`. Keep those unknown ratings visible as gaps even when output text is prefixed to identify its source. The helper may validate and normalize these fields, but it does not score likelihood, estimate probabilities or losses, accept risk, activate controls, notify anyone, or mutate the Program Ledger. Accountable owners decide treatment and acceptance.

## Incident contract

1. Preserve one unique `incident_ref`, incident type, observed state, severity,
   owning responder, and supplied evidence. Unknown facts remain unknown.
2. Separate outage impact, security coordination, continuity concerns,
   backup/recovery options, and communication drafts. A draft is never a sent
   message and an option is never an approved action.
3. Every material observation, impact, recovery option, communication record,
   and closure claim points to supplied evidence. Closure requires evidence
   capture, residual-risk treatment, owner confirmation, and an explicit
   proposed or supplied state; narrative alone is insufficient.
4. Preserve ownership boundaries: the owning responder coordinates response;
   Platform owns platform controls; the Program Ledger owns program state; and
   deployment authority owns deploy and rollback decisions.

## Authority and safety boundary

The helper returns `READY_FOR_OWNER`, `DRAFT`, or `BLOCKED` with empty effects.
Requests to deploy, roll back, isolate, rotate credentials, send, close,
approve, or mutate incident/Program/deployment state fail closed. Customer and
internal communication can be drafted or recorded as supplied evidence only.
Private incident records and credentials are rejected without echoing content.

## Tooling and resumability

Use the native CLI first, a CLI wrapper for deterministic normalization, direct API
only through a consumer-owned exception adapter, and MCP only for a
consumer-authorized persistent session. A specialist or generalist execution
profile may retain only redacted state in `state.jsonl`; no raw transcript,
secret, customer record, or transport payload is persisted. Read
[`references/schemas.json`](references/schemas.json#/definitions/input) and
[`references/schemas.json`](references/schemas.json#/definitions/output),
[`advanced/advanced.md`](advanced/advanced.md), and the eval suite before use.
