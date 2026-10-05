# Pre-Signature Package Readiness Check: active procedure

## Procedure

1. Confirm document version, parties, every exhibit/schedule and whether any comments/redlines remain.
2. Check names, dates, signature blocks and the supplied evidence of signer authority; do not infer authority from title.
3. Review required internal and counsel approvals and identify missing approval evidence or open issues.
4. Draft a signing readiness checklist and proposed routing details (signers/order/CC/archive) for owner review.
5. Do not send, route in e-signature, sign, represent approval, or create a binding act.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
