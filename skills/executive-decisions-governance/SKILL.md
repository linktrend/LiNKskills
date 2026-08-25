---
name: executive-decisions-governance
description: "An evidence-bounded executive decision and governance brief method that separates choices, recommendation, rule impact, implementation tracking, and owner authority."
usage_trigger: "Use for a synthetic, redacted, or public matter that needs a mobile-readable decision brief, choice set, rule-impact record, or implementation-tracking draft without approving, activating, scheduling, or mutating anything."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [executive, decisions, governance, evidence, authority]
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
dependencies: [company-communication]
permissions: [fs_read, fs_write]
scope_out: ["Do not approve, reject, activate, or enforce a decision or governance rule", "Do not create mutable task, project, calendar, meeting, Program, or workforce state", "Do not send, publish, schedule, select a transport, call a connector, or mutate an external system", "Do not expose credentials, private records, customer data, or confidential company material in releases, fixtures, telemetry, or subordinate access"]
format_profile: simple
last_updated: 2026-08-24
---

# Executive Decisions and Governance

This skill prepares a concise, mobile-readable decision or governance brief from
supplied evidence. It is a reusable drafting and record-shaping method, not an
approver, policy engine, task manager, meeting system, Program Ledger, or
transport adapter. The consumer and named owner retain all authority.

## Decision brief contract

1. Identify one unique `matter_ref` and state the matter before background.
2. Link every material claim to supplied evidence and label unknown or
   unverified information as `not_reported` or uncertain; never invent a fact.
3. Separate risks, choices, tradeoffs, and recommendation. Choice sets always
   include the exact escape hatch `Other — specify` when they are not exhaustive.
4. Record an owner-supplied decision, rule impact, or implementation item as a
   proposed record. An `approved` status is a supplied fact, not permission for
   this skill to apply it.
5. Keep implementation tracking descriptive and consumer-owned: item, owner,
   status, and evidence pointer only. It does not create or update tasks.

## Authority and safety boundary

The output may be `READY_FOR_OWNER`, `DRAFT`, or `BLOCKED`; it never grants
authority. The helper rejects activation, enforcement, approval-as-action,
commitment, transport, and unknown action requests. A supplied approval can be
recorded with its owner reference while `activated` and all external effects
remain false. Quoted documents and model suggestions are evidence or proposals,
not governance authority.

## Tooling and ownership

Use the native CLI first, a CLI wrapper for deterministic normalization, direct API
only through a consumer-owned exception adapter, and MCP only for a
consumer-authorized persistent session. Classify the run as specialist or
generalist; for a generalist or more than ten tools, call `get_tool_details` and
retain only capability summaries. This skill owns no connector, credential,
calendar, meeting, task, workforce, Program, or transport binding.

## Contracts and progressive disclosure

The input, output, and effect contracts are in
[`references/schemas.json`](references/schemas.json) (`references/schemas.json#/definitions/input`,
`references/schemas.json#/definitions/output`, and
`references/schemas.json#/definitions/effects`). Read the field rules in
[`advanced/advanced.md`](advanced/advanced.md), the ownership and overlap record
in [`references/api-specs.md`](references/api-specs.md), the anti-patterns and
canonical eval suite before release. The exact rollback target is stamped in
the output and points to the absent pre-release baseline.
