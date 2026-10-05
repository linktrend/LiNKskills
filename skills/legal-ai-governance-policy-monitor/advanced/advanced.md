# AI Governance Policy Change Review: active procedure

## Procedure

1. Confirm the policy/version, prior review date, organization footprint and authorized evidence set; do not assume access to inboxes, chat or private workspaces.
2. Summarize actual practices from supplied records and compare each commitment, approval control and inventory requirement to observed evidence.
3. Classify findings as a factual mismatch needing owner review, a policy ambiguity, a possible improvement or no change; do not mark a policy violation without support.
4. If regulatory changes are cited, verify current authority, effective dates and scope; otherwise tag the citation and required check.
5. Draft a section-level change proposal, evidence coverage statement and policy-owner questions. Do not edit or publish the approved policy.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
