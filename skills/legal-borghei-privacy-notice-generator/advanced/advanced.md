# Privacy Notice Drafting: active procedure

## Procedure

1. Determine notice type, audience, relevant entities, territories, channels and special processing (cookies, AI, transfers).
2. Collect the actual data inventory: categories/sources, purposes, lawful-basis decisions from owner/counsel, recipients/processors, transfers, retention and rights contact.
3. Draft plain-language modular notice text with placeholders for missing facts; distinguish legal basis supplied by counsel from unresolved issue.
4. Check each jurisdiction’s current authoritative notice requirements and use correct separate versions/supplements; do not rely on source-era country checklist as current law.
5. Cross-check notice claims against actual practices and contracts, highlight contradictions and review dates.
6. Return draft and approval checklist. Do not publish, notify data subjects or represent compliance.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve privacy notice generator and GDPR compliance method

## Same-task additions: audience inventory and clause trace

Record the notice audience and type explicitly: public website/app, customer, employee, applicant, vendor/contact, or another supplied group. Build a processing inventory from verified practice facts: controller identity, purpose, data categories and sources, recipients, retention, contact/rights channel, and user context. Map every draft clause to a factual source or mark it as an owner question. For special-category/children's data, tracking, automated decisions, cross-border processing, or high-risk use, branch to the matching legal/privacy assessment; do not assert a legal basis, deadline, or notice duty from memory. Keep an as-of jurisdiction table only when built from current primary authorities for the confirmed scope.
