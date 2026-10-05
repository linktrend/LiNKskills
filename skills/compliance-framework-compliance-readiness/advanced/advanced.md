# Cross-Framework Compliance Readiness: active procedure

## Task boundary

This pack owns point-in-time multi-framework readiness for a named audit window, certification milestone or new-framework launch. Use supplied scope, evidence, dates, owner capacity and auditor-independence facts to identify readiness gaps and milestone-specific next steps. It does not design a standing compliance operating model or annual program calendar; route that request to `compliance-framework-compliance-os`.

## Procedure

1. Confirm a named audit window, certification milestone or framework-launch decision. Route framework-commitment/evidence/calendar/management-review decision packets to `compliance-program-decision-review`. If the request seeks standing portfolio, control/evidence architecture or annual calendar design, route to `compliance-framework-compliance-os`.
2. Confirm whether the task is multi-framework; single-framework readiness is routed to the applicable framework-specific pack while separable cross-framework planning continues.
3. Validate the declared framework set and classify each as law/regulation, customer requirement, voluntary standard or certification objective; unresolved applicability remains conditional.
4. Build a common-control candidate map and evidence reuse plan. For each mapping, state why evidence is equivalent or what framework-specific overlay/sample is still required.
5. Sequence readiness work against dependencies, customer/regulatory priority, control-owner capacity, evidence freshness and auditor independence. Treat timelines as planning assumptions, not guarantees.
6. Review the supplied calendar, audit window, owner capacity and auditor-independence facts for this milestone; identify date/dependency risks and offer only milestone-specific readiness sprint options. Do not author an annual or standing program calendar.
7. Return a milestone-specific readiness packet with evidence tasks, owners, assumptions, auditor-independence gaps and reviewer questions. Do not claim certification readiness or modify a GRC system.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
