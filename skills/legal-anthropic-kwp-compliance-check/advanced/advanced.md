# Initiative Compliance Review: active procedure

## Procedure

1. Define the initiative and distinguish current practice from planned activity, claims and assumptions.
2. Map user/data flows, parties, markets, services and requested review domains; identify missing factual inputs.
3. Use the source checklist areas only when in scope: privacy notice/rights, DPA/processor terms, data retention/transfers, consent, marketing/security and organizational controls.
4. Verify current legal rules and deadlines by jurisdiction with primary sources; the preserved KWP date table is historical source material, not current authority.
5. Prepare evidence-linked findings, risk areas, remediation options and review questions; no final compliance verdict or launch approval.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
