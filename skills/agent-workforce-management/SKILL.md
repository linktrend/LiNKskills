---
name: agent-workforce-management
description: "An evidence-bounded method for defining reusable agent roles, selecting supplied Brain rules, drafting capability and delegation requests, monitoring workload and quality, and proposing safe suspension or retirement without granting authority."
usage_trigger: "Use for a synthetic, redacted, or public workforce matter that needs a role definition, applicable-rule selection, capability request, domain delegation plan, workload/blocker review, quality evaluation, or owner-review suspend/retire proposal."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [agent-workforce, roles, delegation, evidence, suspension]
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
dependencies: [executive-decisions-governance, department-head]
permissions: [fs_read, fs_write]
scope_out: ["Do not activate, suspend, retire, or supervise an agent", "Do not approve Brain rules, technical grants, capability grants, or delegation", "Do not copy credentials, private memory, identity, or account bindings", "Do not call connectors, send messages, schedule work, or mutate workforce, Program Ledger, or external state"]
persistence:
  required: false
  state_model: stateless_single_pass
format_profile: simple
last_updated: 2026-08-24
---

# Agent Workforce Management

This skill prepares evidence-bounded workforce artifacts for owner review. It is a
role and supervision planning method, not an agent runtime, Brain policy engine,
credential store, scheduler, grant approver, or workforce database. The consumer
and named owner retain all authority.

## Workforce contract

1. Define one reusable role with a purpose, domain, boundaries, and evidence.
2. Select only a supplied Brain rule whose applicability is explicit; this skill
   cannot author, approve, activate, or enforce a rule.
3. Draft capability/skill assignment requests with a capability reference,
   purpose, and evidence pointer. A request is not a technical grant.
4. Describe domain delegation with a named owner and evidence. Delegation does
   not activate an agent, create a task, or mutate a Program.
5. Monitor workload, blockers, evidence freshness, quality, and repeated failure
   without copying private memory or exposing credentials.
6. Produce training, skill, authority, suspend, or retire recommendations as
   proposals. A safe suspend/retire proposal is never an action.

The input, output, and empty-effects contracts are in
[`references/schemas.json#/definitions/input`](references/schemas.json#/definitions/input),
[`references/schemas.json#/definitions/output`](references/schemas.json#/definitions/output),
and [`references/schemas.json#/definitions/effects`](references/schemas.json#/definitions/effects).
The complete canonical
eval suite is in [`references/eval-suite.json`](references/eval-suite.json).

## Authority and privacy boundary

Outputs are `READY_FOR_OWNER`, `DRAFT`, or `BLOCKED`; none grants authority.
Unknown, missing, or unreported evidence remains visible as uncertainty. The
helper rejects activation, suspension/retirement actions, technical grant
approval, credential or private-memory copying, connector calls, and unknown
actions. It returns empty `messages_sent`, `external_calls`, and `mutations`.

Credentials, private memory, identity, account bindings, customer records, and
raw confidential workforce records are never retained in releases, fixtures, or
telemetry.

## Tooling and ownership

Use the native CLI first, a CLI wrapper for deterministic normalization owned by
the consumer,
direct APIs only through a consumer-authorized exception, and MCP only for a
consumer-authorized persistent session. For a generalist run or more than ten
tools, inspect tool details and retain capability summaries only. This skill owns
no Brain rule, credential, connector, schedule, agent runtime, technical grant,
Program Ledger, or persistent workforce state.

Read [`advanced/advanced.md`](advanced/advanced.md) for field-level handling,
[`references/api-specs.md`](references/api-specs.md) for ownership and overlap,
and [`references/old-patterns.md`](references/old-patterns.md) before adapting
legacy workforce material. The rollback target is stamped in every output and
points to the absent pre-release baseline.
