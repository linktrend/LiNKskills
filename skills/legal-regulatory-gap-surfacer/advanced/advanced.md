# Regulatory Gap Intake and Surfacing Proposals: active procedure

## Procedure

1. Confirm the supplied policy diff's scope, source, date, verification status, excluded provisions and affected policy versions. Carry every scope-limitation warning into derived records; do not present a partial diff as a complete compliance picture.
2. Verify each cited legal/regulatory source and current status through authorized current primary authorities. Where not verifiable, mark the requirement candidate/unverified and name the exact check; do not transform a candidate into a binding gap.
3. Extract proposed gap items with requirement/source pinpoint, affected policy/process, organization role/scope basis, evidence of current state, confidence, owner role and review date. Separate source facts from inference.
4. Compare only against the supplied register snapshot. Deduplicate on requirement + affected policy/process + scope; retain provenance and explain partial matches rather than silently merging distinct obligations.
5. Prepare add/update proposals with priority rationale, verification state, missing owners/dates and dependencies. Never write the register or close/accept items.
6. Draft an owner notice only when requested and the approved recipient/channel policy is supplied. Show exact proposed recipients and message content for a human to act; do not send, schedule or claim a cadence.
7. Return the intake proposal, dedupe decisions, source coverage, scope limitations, draft notice (if requested), and open counsel/owner questions.

## Completion check

- Every proposed gap is linked to a supplied source and policy/process scope; unverified law stays labeled.
- Register records are proposals only, with no official status changes.
- `external_effects` and `mutations` remain empty; notices are draft text only.
- Full-register status/close/risk-acceptance tasks route to `legal-regulatory-gaps`.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
