# Data Processing Agreement Review: active procedure

## Procedure

1. Confirm DPA direction (customer’s DPA vs vendor’s), party roles and the main agreement; resolve ambiguity before clause interpretation.
2. Map scope/schedules: subject, duration, purpose, data/subjects, instructions, confidentiality, security, subprocessors, rights assistance, breach, DPIA/audit, deletion/return and transfers.
3. Compare each clause with supplied approved playbook and current primary legal requirements for actual jurisdictions; source checklist is not current law.
4. Check consistency with processing facts and privacy notices; flag missing annexes, contradictions and unsupported operational commitments.
5. Draft prioritized risks and redlines/options for counsel, marking unknown obligations and operational feasibility checks.
6. Do not sign, send, accept terms or promise a control.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve GDPR compliance and privacy compliance reviewer

## Same-task additions: processing schedule and transfer evidence

Map the agreement and schedules against confirmed processing facts: controller/processor roles, subject matter, duration, purpose, data and subjects, documented instructions, confidentiality, security, subprocessors, assistance, incident handling, audit, deletion/return, and transfer terms. Record absent schedules and contradictions with exact clause locators. Check any cited current legal requirements only against current primary sources for confirmed jurisdictions and parties; do not treat the upstream GDPR checklist as current or universally applicable law. If destinations, roles, or processing details are unknown, preserve them as open questions and separate contract gap from legal conclusion.
