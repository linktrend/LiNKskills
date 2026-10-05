# Vendor Agreement Status Brief: active procedure

## Procedure

1. Resolve vendor legal name vs trade names and subsidiaries using supplied authoritative identifiers; flag ambiguity.
2. Inventory supplied active, expired, pending, amended and terminated agreements with version, parties and dates.
3. Summarize relationship coverage, service scope, key renewal/expiration dates and open negotiation status only as recorded in source evidence.
4. Cross-reference email/CRM/CLM only if provided through current authorized tools; otherwise list unavailable source sets.
5. Return a status brief with source links and verification gaps; do not contact vendor or update CLM/CRM.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
