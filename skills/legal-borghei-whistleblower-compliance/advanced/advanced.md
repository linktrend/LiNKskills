# Whistleblower Program Applicability and Policy Review: active procedure

## Procedure

1. Map actual entities, workforce, territories, headcount bands and sectors before assessing any directive/statute; verify current transposition and scope from primary sources.
2. Review reporting channel availability, independence, accessibility, anonymity/confidentiality claims, acknowledgment, investigation and anti-retaliation processes.
3. Assess privacy and retention handling for reporter/subject data and conflicts in investigator assignment.
4. Identify gaps and propose policy/process language only as a draft; mark each legal requirement and deadline for current verification.
5. Route allegation handling or active investigation to authorized counsel/HR process. Do not investigate individuals, notify subjects, disseminate policy or promise anonymity.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
