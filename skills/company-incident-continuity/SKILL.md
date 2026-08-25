---
name: company-incident-continuity
description: "An evidence-bounded incident and continuity coordination method for outage, security, recovery, communication, evidence capture, and closure review."
usage_trigger: "Use for synthetic, redacted, or public incident evidence when an owner needs a concise outage/security/continuity review or recovery and closure proposal without deployment, communication, credential, or authority mutation."
version: 1.0.0
release_tag: v1.0.0
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
last_updated: 2026-08-25
---

# Company Incident and Continuity Management

This skill prepares an evidence-bound coordination artifact for an outage,
security incident, continuity concern, or recovery review. It is not an
incident commander, deployment controller, security authority, customer
messaging service, backup system, Program Ledger, or durable incident store.

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
[`advanced/advanced.md`](references/advanced.md), and the eval suite before use.
