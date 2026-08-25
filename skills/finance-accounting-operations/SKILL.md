---
name: finance-accounting-operations
description: "Read-only finance and accounting operations for cash-flow forecasts, budget versus actuals, invoice/payment/expense tracking, close preparation, runway risk, and approval-boundary decisions from an approved Odoo contract."
usage_trigger: "Use when a Principal needs an evidence-labeled finance operations brief from supplied Odoo contract data, without changing accounting records or invoking a connector."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-24
author: LiNKskills Library
tags: [finance, accounting, odoo, operations, read-only]
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
dependencies: [revenue-adapter-base, studio-controller]
permissions: [fs_read, fs_write]
scope_out: ["Do not invoke an Odoo connector or direct API", "Do not create or mutate a ledger, accounting system, journal, invoice, payment, expense, budget, or approval", "Do not handle credentials, private company data, or make tax, legal, or accounting-finality claims"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-08-24
---

# finance-accounting-operations

This skill turns an approved consumer-provided Odoo snapshot into a clearly
labeled operations brief. It is an analysis and preparation layer, not an Odoo
client, ledger, accounting system, or authority to act.

## Decision Tree (Fail-Fast & Persistence)

0. Resume only from the matching `.workdir/tasks/*/state.jsonl` checkpoint.
1. Validate the input contract, period, currency, source references, and data classification.
2. Validate the approved Odoo contract identifier/version and its declared read operations. Missing, stale, or ambiguous contract metadata is `PENDING_APPROVAL`.
3. Validate the intelligence floor and the CLI-first protocol: native cli, cli wrapper, direct api, mcp. This skill may describe a consumer adapter, but it never calls one.
4. Classify the request as `Specialist` or `Generalist`; for `Generalist` or more than ten tools, call `get_tool_details` and cache only capability summaries.
5. Build only requested read-only views: cash-flow forecast, budget versus actual, invoice/payment/expense status, close preparation, runway, and risk.
6. Preserve source references, period, currency, assumptions, missing data, and confidence on every material conclusion. Do not invent balances, dates, rates, or counterparties.
7. If the operator asks to post, edit, pay, approve, reconcile as final authority, activate, or bypass a control, refuse that effect and return `PENDING_APPROVAL` with the owning consumer or Principal identified.
8. Validate the output contract, effect declaration, provenance, and rollback metadata; write artifacts only under the task-local work folder; append the completion checkpoint.

## Scope-In

- Forecast cash inflows and outflows from supplied, normalized source records; show assumptions and a range rather than false precision.
- Compare supplied budgets with actuals by period, category, and currency while preserving unmatched and excluded lines.
- Track invoice, payment, and expense status as observations; flag duplicates, missing references, overdue indicators, and unresolved mismatches.
- Prepare a close checklist and runway/risk brief; distinguish evidence, inference, and an operator decision request.
- Use the approved Odoo tool/API contract as an interface declaration only. The owning consumer supplies snapshots and owns transport, credentials, endpoint/model mapping, and mutations.

## Scope-Out and Authority Boundary

- Never invoke Odoo, create a connector, request or store credentials, or make a network call.
- Never create or mutate a private ledger, accounting database, journal entry, invoice, payment, expense, budget, pointer, release, or approval.
- Never claim tax, legal, audit, GAAP, statutory, or accounting-final authority. Escalate to the Principal or qualified owner when that authority is requested.
- Never include customer, company-private, credential, or live-account data in examples, fixtures, telemetry, or release content.
- Never finalize a recommendation when the contract, period, currency, source provenance, or material variance is unresolved.

## Tooling Protocol (CLI-First)

1. Level 1 — Native CLI: inspect task-local, synthetic or consumer-supplied snapshots.
2. Level 2 — CLI wrapper: perform deterministic grouping, variance, ageing, and range calculations through `scripts/helper_tool.py`.
3. Level 3 — Direct API: not permitted by this skill; the consumer adapter owns any approved transport.
4. Level 4 — MCP: not permitted for execution or persistence; a consumer may use a separate governed adapter and pass back an exact snapshot.

## Internal Persistence (Zero-Copy / Flat-File)

- Append checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Store only task-local report artifacts and redacted provenance; never copy credentials or live private records into the release.
- A checkpoint is resumable only when the same task ID and input digest are supplied.

## Workflow

### Phase 1: Intake and contract gate

1. Read the input contract from `./references/schemas.json#/definitions/input`.
2. Confirm the approved Odoo contract ID/version, snapshot digest, period, currency, requested views, and synthetic/redacted classification.
3. If any gate fails, checkpoint `PENDING_APPROVAL` and stop before calculation.

### Phase 2: Deterministic analysis

4. Calculate forecast range, budget/actual variance, status counts, close blockers, runway assumptions, and risk flags.
5. Keep observations separate from inferences; retain source references and unmatched records.
6. Use `studio-controller` for review and close-control prompts only; do not duplicate its controls or create a system of record.

### Phase 3: Approval boundary

7. Present proposed next steps as a request for the owning consumer or Principal.
8. Refuse or pause any request to mutate an Odoo record, issue an approval, or bypass a segregation-of-duties control.

### Phase 4: Output and checkpoint

9. Validate `finance_operations_brief` at `./references/schemas.json#/definitions/output`.
10. Include an explicit empty external-effects declaration, source provenance, exact release identity, and rollback reference.
11. Append `COMPLETED` only for a validated read-only brief; otherwise append `PENDING_APPROVAL` or `FAILED`.

### Phase 5: Ledger and trace protocol

12. Append the standard redacted invocation event to the repository execution ledger through the runtime, without writing finance records.
13. Save a trace under the task-local state directory; update `references/old-patterns.md` only when a new failure mode is confirmed.

## Contracts

| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `finance_operations_input` | `./references/schemas.json#/definitions/input` | Validate an approved-contract snapshot and requested read-only views. |
| **Output** | `finance_operations_brief` | `./references/schemas.json#/definitions/output` | Return evidence-labeled finance observations with no external effects. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable gates and the input digest. |

## Progressive Disclosure References

- Advanced calculations and escalation: `./advanced/advanced.md`
- Odoo boundary, candidate review, and release provenance: `./references/api-specs.md`
- Known anti-patterns: `./references/old-patterns.md`
- Version history and rollback: `./references/changelog.md`
- Synthetic traces: `./examples/success-pattern.md` and `./examples/error-recovery.md`
