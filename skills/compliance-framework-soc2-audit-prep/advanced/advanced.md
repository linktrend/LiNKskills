# SOC 2 Type II Readiness Review: active procedure

## Procedure

1. Confirm service/system boundary, selected Trust Services Criteria, subservice treatment, auditor expectations and declared observation period.
2. Map each in-scope criterion to controls, owners, test evidence and periods. Do not assume optional criteria or auditor tolerances.
3. Sample controls across the observation period and record gaps, outages, control changes, exceptions and evidence provenance.
4. Assess whether control operation is evidenced consistently; distinguish design evidence from operating effectiveness evidence.
5. Prepare exception/remediation questions and an evidence collection plan. Do not predict an auditor opinion or claim SOC 2 certification.

## Source-specific six-question coverage

Keep the source Type II prompts: (1) system boundary and selected Trust Services Criteria; (2) control cycles missed during the defined observation period; (3) change evidence for controls introduced mid-period; (4) exception population and materiality basis; (5) criterion coverage at the period start as well as later samples; and (6) a carefully justified ISO 27001 crosswalk. The service auditor defines testing and opinion; do not present these prompts as audit acceptance criteria.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
