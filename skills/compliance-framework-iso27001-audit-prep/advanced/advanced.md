# ISO 27001 ISMS Audit Preparation: active procedure

## Procedure

1. Confirm the ISMS scope, declared standard edition, audit type/period and exclusions from controlled records.
2. Review risk assessment, treatment plan and Statement of Applicability traceability; identify controls selected, excluded, or lacking rationale/evidence.
3. Sample access, suppliers, incident response, logging, change and corrective-action evidence; cite time window/population and preserve counterevidence.
4. Build audit coverage against the required clauses/control set and check auditor independence and prior finding follow-up.
5. Report evidence gaps, stale records and questions for the owner; do not import source-era cross-framework overlap percentages.
6. Draft internal readiness findings only; do not certify or attest to conformity.

## Source-specific six-question coverage

Keep the source audit prompts: (1) stated ISMS scope and rolling coverage across the declared audit cycle; (2) risk-register freshness and treatment-to-control traceability; (3) periodic access-review evidence; (4) supplier inventory and review evidence; (5) incident handling and post-incident review; and (6) management-review inputs, outputs and follow-up. Confirm the current standard edition, SoA and audit scope; source sampling cadence is not automatically a company requirement.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
