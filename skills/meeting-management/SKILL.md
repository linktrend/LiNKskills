---
name: meeting-management
description: "Evidence-bounded meeting preparation, notes processing, decision routing, and follow-up verification without retaining private transcripts or owning destination systems."
usage_trigger: "Use when a supplied meeting needs an agenda, private pre-brief, redacted notes, decision and commitment extraction, routing references, or follow-up verification."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [meetings, agendas, decisions, follow-up, evidence, privacy]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [research, company-communication]
permissions: [fs_read, fs_write]
scope_out: ["Do not retain or expose raw private transcripts", "Do not send invitations, messages, minutes, or tasks", "Do not mutate Google, Brain, Program, Calendar, or agent stores", "Do not infer a decision, commitment, acknowledgement, or completion without evidence"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
format_profile: heavy
last_updated: 2026-08-24
---

# Meeting Management

Meeting Management is a store-independent preparation and reconciliation
contract. It evaluates maintained meeting candidates, prepares an agenda and a
private pre-brief, processes only supplied redacted notes or transcript
references, extracts decisions/commitments/tasks, preserves opaque routing
references, and verifies follow-up evidence. The consumer owns the meeting
record, destination stores, calendar, messaging, permissions, and delivery.

## Decision tree

1. Resume only the matching task checkpoint and request identity. Confirm the
   meeting reference, purpose, owner, participants as synthetic labels,
   evidence provenance/licence, privacy class, and requested mode.
2. Reject or redact raw private transcript text, credentials, personal data,
   privileged material, or live account details before reasoning. A transcript
   reference and bounded excerpt hash may be retained; the raw body never is.
3. Separate supplied facts, cautious inferences, open questions, and proposed
   actions. A proposal is not a decision, an assigned follow-up is not proof of
   acknowledgement, and an agent's statement is not completion evidence.
4. Prepare or reconcile locally. Sending invitations, distributing notes,
   creating tasks/events, assigning work, changing a destination record, or
   making a commitment requires the owning consumer authority and returns
   `PENDING_APPROVAL`.

## Meeting workflow

Agenda output states objective, desired decision, time-boxed items, required
evidence, participants/roles, dependencies, and a parking lot. A private
pre-brief is clearly marked private, contains questions and risk prompts, and is
not routed to shared notes. Notes processing returns a concise redacted summary
with evidence pointers; it never copies a raw transcript into a release,
telemetry, Brain, or a follow-up payload.

Decisions retain a stable synthetic reference, statement, owner/authority,
evidence pointer, confidence, and unresolved alternatives. Commitments and
tasks retain an owner, desired result, deadline if supplied, dependency,
destination mapping (Google/agent/Program), and follow-up state. A `Verified`
follow-up requires a consumer verification receipt; otherwise use `Awaiting
evidence`, `Blocked`, or `Proposed`. Routing is reference-only and never writes
the destination.

Maintained-candidate review checks owner, purpose, recent evidence, attendance,
decision value, duplication, and next review date. It may recommend maintain,
review, or retire, but cannot retire or mutate the schedule. Decisions always
offer `Other — specify` and state the authority boundary.

## Tooling, persistence, and proof

Classify specialist or generalist work; use native CLI, then a narrow CLI
wrapper (a cli wrapper), approved direct API exception, and MCP only for a
persistent adapter.
Persist only redacted checkpoints and hashes. Effects are always empty in this
provider release. Source, consumer, hosted, E2E, and production proof remain
distinct; a local contract test never proves meeting delivery or live-store
mutation.

## Contracts

| Direction | Artifact | Schema |
| --- | --- | --- |
| Input | `meeting_request` | `./references/schemas.json#/definitions/input` |
| Output | `meeting_management_result` | `./references/schemas.json#/definitions/output` |
| State | `meeting_state` | `./references/schemas.json#/definitions/state` |

## Migration boundary

This family reuses research and communication primitives without duplicating
their stores or authority. It does not own Time Management task state, Executive
Decisions governance, Google Workspace credentials, Calendar scheduling,
transcript storage, Brain knowledge, or Program Ledger mutations.
