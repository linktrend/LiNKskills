# Privacy Regulation Gap Analysis: active procedure

## Procedure

1. Establish processing and territorial footprint; assess role, threshold, sector and exceptions for each proposed regime.
2. Research current primary law and official guidance before extracting requirements; distinguish binding law, regulator guidance and standards.
3. Build requirement records and map them to supplied policy/control evidence, assigning supported/partial/unknown/not-applicable states.
4. Prioritize verified gaps by consequence, timing and dependency; show source and date for each legal claim.
5. Draft remediation and evidence needs with owners and open counsel questions. Do not certify compliance or change privacy policies.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve GDPR compliance and privacy compliance reviewers

## Same-task additions: source-bound obligation records

Record each requirement with a specific authority or supplied policy identifier, version/date, jurisdiction, actor, trigger, required action/evidence, and applicability basis. Map it to a named control and evidence artifact with owner, evidence date, and status `supported`, `partial`, `missing`, `unknown`, or `not_applicable`; explain why. Distinguish a legal obligation from regulator guidance, contract promise, internal policy, and voluntary standard. A missing artifact is an evidence gap, not proof the control is absent; a cited upstream checklist is not a current law source.
