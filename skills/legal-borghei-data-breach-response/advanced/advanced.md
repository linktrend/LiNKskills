# Personal Data Breach Response Analysis: active procedure

## Procedure

1. Preserve incident facts and timestamp provenance; distinguish discovery time, event window, containment and unknown duration.
2. Assess impact factors from the source methodology (data context, identification ease, circumstances, confidentiality/integrity/availability and safeguards) as a structured draft, not an automatic severity verdict.
3. Identify affected data subjects, entity roles, jurisdictions and contracts. Verify each possible notification rule, clock and recipient against current primary sources; do not reuse source thresholds as current law.
4. Prepare a candidate notification decision matrix and list evidence gaps, counsel decisions and insurer/customer dependencies.
5. Draft response options and an incident timeline for counsel/security review. No containment action, notification, regulator contact or incident log mutation.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
