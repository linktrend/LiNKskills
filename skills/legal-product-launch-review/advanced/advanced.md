# Product Launch Legal Review: active procedure

## Procedure

1. Freeze product/version, scope, intended launch markets, channels, audience and evidence cutoff date.
2. Review supplied materials by relevant legal categories (privacy, consumer claims, IP, accessibility, AI, safety, terms/contracts, regulated-sector issues).
3. Use the source seven-category method from preserved reference; include only applicable categories and retain unsupported categories as unknown.
4. Cross-link findings to specialized reviews (marketing claims, privacy impact, vendor/AI contracts); avoid duplicate conclusions and confirm evidence source.
5. Verify current authority and territorial scope for each legal issue. Treat source category framework as method, not law.
6. Draft launch review with blockers/questions/conditions for accountable owner and counsel. Do not approve, publish or alter release systems.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
