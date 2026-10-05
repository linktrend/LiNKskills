# Rapid Product/Legal Concern Triage: active procedure

## Procedure

1. Clarify the actual behavior, affected user, scale, severity and immediate risk; avoid solving a different hypothetical.
2. Apply source-defined quick triage categories only as internal screening, not legal conclusion. Explain why the signal was chosen.
3. Check high-consequence triggers: safety/privacy harm, regulator contact, public claim, legal dispute, vulnerable people or irreversible effect.
4. If a trigger or fact gap requires depth, route to the dedicated feature, launch, privacy or legal task and preserve quick triage result as provisional.
5. Return concise signal and one or two next steps. Never mark a product “safe” or issue launch approval.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
