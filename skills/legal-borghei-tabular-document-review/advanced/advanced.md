# Multi-Document Legal Data Extraction Matrix: active procedure

## Procedure

1. Define extraction columns precisely and select document types; preserve user-defined labels and stable document IDs.
2. Inventory only supplied/known authorized files; no directory scanning or source-script execution. Record unreadable/scanned files as inaccessible.
3. Extract each requested field from each document with page/section/paragraph pinpoint, literal value, normalized value when justified, confidence and ambiguity note.
4. Keep one row per source document; detect duplicates, missing fields, conflicts, inconsistent units/dates/entities and unlinked values without resolving legal meaning.
5. If multiple reviewers or batches are available, divide work by document set only under authorized parent supervision and reconcile through IDs; do not spawn agents by default.
6. Return matrix plus low-confidence review queue, coverage count and exceptions. This is extraction, not legal risk analysis or redlining.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
