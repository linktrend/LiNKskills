# ISO 13485 QMS Audit Preparation: active procedure

## Procedure

1. Confirm QMS boundary, product/site population, audit stage and the exact standard/regulatory versions to be assessed.
2. Review representative design-history samples for requirements-to-verification/validation traceability and identify missing evidence; do not assume clinical or regulatory acceptance.
3. Sample CAPA root cause/effectiveness, process validation, risk-management files, post-market trends and complaint handling using supplied records.
4. Record sampling method and limits, open findings, aging and repeat themes. Separate ISO management-system requirements from market-specific device regulations.
5. Draft a readiness plan with source-linked gaps and owners. Certification, recall/reportability, and product release decisions remain with qualified owners.

## Source-specific six-question coverage

Preserve the source sampling prompts: (1) three sampled design-history files with design verification/validation traceability; (2) five recent CAPAs with effectiveness evidence; (3) process-validation revalidation status; (4) risk-management file for the highest-risk product; (5) recent post-market surveillance evidence; and (6) management-review evidence against the declared edition's inputs/outputs. These are sample prompts, not an assurance sample size or certification criterion.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
