# Technology Contract Negotiation Position Plan: active procedure

## Procedure

1. Confirm agreement type, parties, service, commercial objectives, deal complexity facts and negotiation stage.
2. Extract current clauses and compare against supplied target/fallback/bright-line positions; do not invent standard positions or market norms.
3. Use three-position framing (counterparty-favorable, balanced, company-favorable) only where supported by approved playbook and business objectives.
4. Prepare objection responses using acknowledgement, evidence/business rationale, alternatives and escalation of bright lines; keep regulatory leverage limited to verified current requirements.
5. Track concessions across revisions and recalculate dependencies, liability, data protection, IP, payment, SLA and termination effects.
6. Return draft negotiation plan, proposed language/positions, unresolved decisions and escalation items. Do not negotiate, send or bind the company.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve technology-contract negotiator and contract-intelligence workflow

## Same-task additions: positions and linked trades

For each negotiation issue, record current clause, stated objective, owner-approved opening/target/fallback, any walk-away or escalation trigger only if supplied, and rationale tied to deal context. If positions are absent, leave them unresolved instead of generating monetary or “market” thresholds. Bundle linked concessions (for example, liability with insurance/SLA, or IP with deliverables/payment) into a give/get table with dependency and fallback. Draft objection options in graduated order: acknowledge, explain the supplied business context, offer a supported alternative, and identify the owner/counsel escalation point. Confirm law/forum and party roles from task input; examples tied to German/EU law remain conditional and require current primary-source verification.
