# Regulatory Feed Review and Change Digest: active procedure

## Procedure

1. Confirm approved watchlist, materiality criteria, source set and last review; do not claim to poll feeds without current access.
2. Prefer official regulator/legislative sources; record publication/update dates, rulemaking stage and primary link for each candidate item.
3. Classify final, proposed, consultation, guidance, enforcement and withdrawn items separately; verify status before presenting urgency or deadline.
4. Screen potential company relevance using supplied footprint and role facts; mark hypothetical impact clearly.
5. Draft a concise digest with source coverage, candidate actions, dates to verify and handoffs. No automatic policy-gap insertion, notification or comment decision.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
