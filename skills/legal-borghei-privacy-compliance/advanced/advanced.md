# Multi-Regime Privacy Compliance Review: active procedure

## Procedure

1. Map processing activities, data subjects, categories, actors and geographies; assess each proposed regime’s territorial and material scope separately.
2. Review supplied controls and evidence for notices/transparency, lawful basis/consent, rights handling, retention, security, international transfers and processors.
3. Use the source’s DPA and DSR lifecycle checklists as issue prompts, not legal proof; route full DPA negotiation or DSAR response to the dedicated pack.
4. Verify legal requirements, timelines and authority guidance by current primary sources. Never treat “global” checklists as universally applicable.
5. Record evidence-supported status, unknowns, gaps, owners and dependencies; no deletion, DSR fulfillment, notice publication or compliance certification.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
