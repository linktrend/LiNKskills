# GDPR DPIA Threshold and Assessment Draft: active procedure

## Procedure

1. Confirm processing description, actors, purposes, data, affected groups, scale, territory and design stage.
2. Research current official DPIA threshold criteria for the stated jurisdictions; do not treat source checklists or thresholds as law.
3. Assess necessity/proportionality and less intrusive alternatives from supplied facts; record missing purpose/retention/legal-basis evidence.
4. Identify risks from data-subject perspective, cite evidence and distinguish likelihood/severity from confidence. Draft safeguards and residual risk.
5. Flag any possible prior-consultation or counsel decision only after current-law verification; do not declare a DPIA legally required or approved.
6. Return a draft assessment and owner/counsel questions.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
