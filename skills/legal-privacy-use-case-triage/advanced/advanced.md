# Privacy Processing Use-Case Triage: active procedure

## Procedure

1. Clarify operation, purpose, data, data subjects, scale, territories, parties and product stage.
2. Check supplied internal policy/registry and identify whether the use case is within approved scope; do not update records.
3. Screen for sensitive/vulnerable data, monitoring, automated decisions, new purpose, transfers and high-impact processing.
4. Verify any mandatory PIA/DPIA threshold with current jurisdiction-specific primary law; route to legal privacy PIA/DPIA task where needed.
5. Return a conditional proceed-to-review/assessment-needed/restrict-pending-facts/stop-for-owner-decision route with safeguards and open questions.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve privacy compliance advisor use-case branch

## Same-task addition: processing purpose and scope map

Capture purpose, data subjects, categories/sensitivity, source, systems, recipients, retention, geography/transfers, claimed legal basis (as a claim, not a determination), controller/processor roles, product stage, and affected decisions. Mark missing fields and compare only with supplied policies and confirmed product facts. Route a potential impact-assessment question to `legal-privacy-pia-generation`; route an actual requirement-to-control mapping to `legal-privacy-reg-gap-analysis`; route agreement terms to `legal-privacy-dpa-review`. Keep foreign data locations and legal applicability unresolved until confirmed.
