# Regulatory Requirement-to-Policy Diff: active procedure

## Procedure

1. Confirm rule text/current status, jurisdiction, effective dates and organization role from authoritative sources and supplied facts.
2. Extract concrete obligations into traceable requirements with definitions, actor, trigger, action and exceptions.
3. Map each requirement to exact approved policy passages; classify covered, partial, absent, conflicting or not applicable with rationale.
4. Keep policy coverage separate from operational implementation; identify evidence needed to test whether written policy matches practice.
5. Draft a diff report and candidate policy-update questions. No source policy edits or compliance certification.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
