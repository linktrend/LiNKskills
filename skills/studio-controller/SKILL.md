---
name: studio-controller
description: "Reusable finance review and close-control primitive for checking evidence, variances, assumptions, and escalation boundaries without owning a ledger, connector, or accounting system."
usage_trigger: "Use when a finance operations brief needs controller-style review, close preparation, variance escalation, or separation of observation from approval."
version: 1.1.0
release_tag: v1.1.0
created: 2026-02-25
author: LiNKskills Library
tags: [finance, controller, close, review]
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
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["Do not create or mutate a ledger, accounting system, journal, invoice, payment, expense, budget, or period lock", "Do not invoke a connector or direct API", "Do not make tax, legal, audit, or accounting-finality claims"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-08-24
---

# studio-controller

`studio-controller` is a review primitive. It checks supplied finance
observations and close evidence, identifies variance and missing support, and
routes a decision to the owning consumer or Principal. It does not own a
system of record and does not call Odoo, Supabase, Vault, or any other service.

## Decision Tree (Fail-Fast & Persistence)

0. Resume only from the matching `.workdir/tasks/*/state.jsonl` checkpoint.
1. Validate the input period, currency, source references, and data classification.
2. Confirm the source is an approved, bounded snapshot; reject credentials and live private fixtures.
3. Validate the intelligence floor and tooling protocol: native cli, cli wrapper, direct api, mcp.
4. Classify execution as `Specialist` or `Generalist`; if `Generalist` or more than ten tools, call `get_tool_details` and cache capability summaries.
5. Review reconciliation status, variance explanations, close blockers, and evidence quality.
6. Separate observed values, inferences, assumptions, unknowns, and operator decisions.
7. Escalate material mismatches, stale data, missing support, or requested mutations as `PENDING_APPROVAL`.
8. Validate the output contract, empty external-effects declaration, provenance, and checkpoint before completion.

## Scope-In

- Review cash-flow, budget/actual, invoice/payment/expense, and close-preparation observations supplied by another skill or consumer.
- Check that each material conclusion has a source reference, period, currency, assumption label, confidence, and owner.
- Prepare a controller-style variance table and a close checklist without declaring the period finally closed.
- Reuse this control language from `finance-accounting-operations`; that skill owns the family workflow and Odoo contract boundary.

## Scope-Out

- Do not write or maintain a private ledger, journal, accounting database, or mutable finance state.
- Do not create, edit, approve, settle, post, or delete any Odoo or accounting record.
- Do not invoke an Odoo, Supabase, Vault, MCP, or direct API connector.
- Do not provide final tax, legal, statutory, audit, or accounting authority.
- Do not hide a mismatch, treat unavailable data as zero, or infer approval from operator urgency.

## Tooling Protocol (CLI-First)

1. Level 1 - Native CLI: read task-local or consumer-supplied snapshots.
2. Level 2 - CLI Wrapper Scripts: perform deterministic variance and checklist preparation.
3. Level 3 - Direct API: not permitted; a separately owned consumer adapter supplies snapshots.
4. Level 4 - MCP: not permitted for execution or persistence.

## Internal Persistence (Zero-Copy / Flat-File)

- Append checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Store only redacted, task-local review artifacts and provenance.
- Do not copy credentials, customer data, or company-private records into the release or trace.

## Workflow

### Phase 1: Intake & checkpointing

1. Read the input contract at `./references/schemas.json#/definitions/input`.
2. Validate source digest, period, currency, and redacted/synthetic classification.
3. Append `INITIALIZED` and stop with `PENDING_APPROVAL` when a gate is missing.

### Phase 2: Review & reasoning

4. Reconcile only on stable references, period, currency, and amount.
5. Categorize every item as `OBSERVED`, `INFERRED`, `MISSING`, or `CONFLICTING`.
6. Build a variance table and close checklist; preserve unresolved items.

### Phase 3: Approval boundary

7. For a material mismatch, stale snapshot, or requested mutation, return a typed owner/escalation request.
8. Never turn a review into a posting, approval, period close, or source mutation.

### Phase 4: Finalization

9. Validate `controller_review` at `./references/schemas.json#/definitions/output`.
10. Include provenance and `external_calls: []` / `mutations: []`.
11. Append `COMPLETED` only when review evidence is sufficient; otherwise checkpoint the typed failure.

### Phase 5: Ledger and trace protocol

12. Use the standard redacted runtime invocation event for telemetry; never write finance records.
13. Add a new confirmed failure mode to `references/old-patterns.md` only after the task is resolved.

## Contracts

| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `controller_review_input` | `./references/schemas.json#/definitions/input` | Validate a bounded finance observation set. |
| **Output** | `controller_review` | `./references/schemas.json#/definitions/output` | Return review findings and typed escalation without side effects. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable review state. |

## Progressive Disclosure References

- Advanced review logic: `./advanced/advanced.md`
- Interface and ownership notes: `./references/api-specs.md`
- Known anti-patterns: `./references/old-patterns.md`
- Version history and rollback: `./references/changelog.md`
