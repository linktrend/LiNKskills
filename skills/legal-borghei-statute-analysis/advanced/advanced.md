# Statute and Regulation Interpretation Workpaper: active procedure

## Procedure

1. Confirm primary source, full text, jurisdiction, amendment/version status and as-of date; do not rely on an unofficial fragment alone.
2. Read title, scope, definitions, exceptions, effective dates and transitional provisions before applying a rule.
3. Extract mandatory, permissive and prohibitory language into who/what/trigger/standard fields; distinguish operative text from guidance.
4. Resolve every cross-reference chain and determine whether it modifies, limits or supplements the provision. Record circular/unavailable references.
5. Apply the extracted text to supplied entity role and facts, presenting competing readings and uncertainty rather than a definitive opinion.
6. Return a cite-linked workpaper and counsel research questions; no legal advice or filing.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
