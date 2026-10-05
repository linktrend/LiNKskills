# Data Subject Request Response Preparation: active procedure

## Procedure

1. Record request and receipt time with source/time zone; determine request type and whether clarification or identity verification is needed.
2. Confirm actual controller/processor role, requester location and applicable law; verify current deadlines and extension rules before calculating a due date.
3. Plan searches against the supplied systems/data map and record each owner/query/result; do not claim a complete search where access is missing.
4. Review possible retention, legal-hold, third-party or other exemption issues only with evidence and counsel; do not delete or disclose data.
5. Prepare acknowledgment, clarification request or substantive draft response with requested-right status, evidence gaps and verified rights information.
6. Escalate minors, employee disputes, broad scope, sensitive data, regulator inquiries, cross-border conflicts, litigation holds and unusual exemptions.
7. No identity verification action, system search outside granted access, erasure, disclosure, response sending or official tracker update.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve privacy compliance advisor data-subject request branch

## Same-task addition: verified request state and search plan

For each request, record requested right, channel, received timestamp and time zone, identity-verification status, confirmed controller/processor role, requester location, scope, and systems/owners needed for a search. Calculate a due date only after the governing jurisdiction and current rule, receipt date, and any supported pause/extension facts are verified. If any input is unknown, return the supported acknowledgment/clarification draft and mark deadline/search completion unresolved. Never access unapproved systems, erase/disclose data, or send the response.
