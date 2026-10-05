# FDA Quality-System Audit Preparation: active procedure

## Procedure

1. Confirm device/product scope, marketed territories, company role and the exact audit or inspection event. Treat applicability and current transition dates as verification inputs.
2. Consult current official FDA sources for the operative quality-system rule, effective dates and any transition; do not repeat source-era dates as current fact.
3. Review supplied QMS samples in the source method’s areas: complaints/adverse events, design history and traceability, process validation, device history records, supplier controls, CAPA effectiveness and audit follow-up.
4. Record each sample’s population, period, evidence locator, result and missing records; distinguish no evidence provided from evidence of nonconformance.
5. Prepare inspection/readiness questions and proposed owners/dependencies. Do not make reportability/recall determinations or file, submit, certify or communicate with FDA.
6. Deliver a draft evidence matrix and prioritized gaps for quality/regulatory counsel review.

## Source-specific six-question coverage

Use these as source-derived sample prompts only after verifying the currently operative FDA rules, transition and applicable device scope: (1) complaint sample plus any required MDR evidence; (2) process-validation qualification and revalidation evidence; (3) representative device-history records for distributed products; (4) CAPA effectiveness samples; (5) current labeling review; and (6) response/closure evidence for any Form 483 or other inspection finding. Source-era lookback windows and citations are not a substitute for current criteria.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
