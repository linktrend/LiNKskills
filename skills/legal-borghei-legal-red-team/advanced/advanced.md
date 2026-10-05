# Adversarial Legal Draft Verification: active procedure

## Procedure

1. Freeze the exact draft/version and define what verification is in scope; do not rewrite the target before recording issues.
2. Decompose it into factual assertions, quotations, legal propositions, calculations, inferences and recommendations.
3. Verify each factual claim against cited record pinpoints and each legal claim against current primary authority; mark unsupported/unavailable instead of inferring correctness.
4. Recalculate arithmetic independently and flag unsupported causal, confidence, speculation and absolute-language leaps.
5. Rank issues by potential consequence and distribution exposure; distinguish factual defect, citation defect, ambiguity and style.
6. Return issue register with exact text/location, evidence, severity rationale and repair suggestion. No claim of complete verification beyond reviewed sources.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
