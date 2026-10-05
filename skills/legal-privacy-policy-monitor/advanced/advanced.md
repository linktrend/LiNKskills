# Privacy Policy Practice-Diff Review: active procedure

## Procedure

1. Confirm approved policy version, prior sweep, covered products and accessible evidence set.
2. Extract actual changes to collection, purpose, sharing, retention, user controls, automated use, vendors and transfers from supplied records.
3. Compare commitments to practice; classify mismatch, policy silence, no-change or unknown without assuming legal significance.
4. Verify any proposed legal disclosure requirement and applicability using current primary authority; retain official source/date.
5. Draft section-level change proposals and owner questions; do not edit or publish the notice or send user notices.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
