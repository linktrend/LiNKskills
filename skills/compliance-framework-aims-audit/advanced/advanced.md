# AI Management System Audit Readiness: active procedure

## Procedure

1. Confirm the declared AIMS boundary, covered systems, audit period, criteria version and independent reviewer; do not infer certification scope.
2. Read the supplied management-system evidence against the source method’s Clauses 4–10 structure: context, leadership, planning, support, operation, performance evaluation and improvement.
3. Review AI risk records, objectives, controls, monitoring and corrective actions; trace each conclusion to evidence and record stale/missing samples.
4. Draft an internal-audit coverage plan with auditor-independence constraints and prior-year follow-up; do not state that evidence meets certification requirements without an auditor decision.
5. Identify reusable evidence across other declared frameworks only when the control objective and acceptance criteria genuinely align; do not assert reuse acceptance by a certification body.
6. Return clause evidence status, gaps, risk treatment questions and an owner-ready readiness draft. Keep certification verdict conditional.

## Source-specific six-question coverage

Retain the source audit questions as a coverage checklist: (1) does the AIMS scope include all relevant AI systems; (2) does the AI policy address lawful and beneficial use, human oversight and continual improvement; (3) are risks covered by the risk register and mapped to applicable Annex A controls; (4) was risk reassessed after material system/model change; (5) is the Clause 9.2 internal-audit plan sufficiently independent; and (6) is the AIMS integrated with existing ISMS/QMS work or duplicated? Verify standard edition, scope and clause text before drawing conclusions.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
