# Marketing Claims Substantiation Review: active procedure

## Procedure

1. Freeze exact text, visuals, placement, audience, territory and product version.
2. Extract every express, implied, comparative, absolute and performance claim; classify claim type and identify a measurable interpretation.
3. Match each non-puffery claim to competent supplied substantiation, population, date, method, limits and claim scope.
4. Review qualifiers, disclosures, net impression, comparative basis and consumer interpretation; do not infer support from source citations alone.
5. Verify current applicable advertising law/guidance and platform rules; note jurisdiction and as-of date or leave unresolved.
6. Suggest narrow revisions and evidence needs for legal/marketing review. Do not clear, publish or approve the campaign.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
