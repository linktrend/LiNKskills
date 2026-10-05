# AI Use Case Governance Triage: active procedure

## Procedure

1. Clarify actual use, users, decision influence, affected groups and whether the system is proposed, piloted or deployed.
2. Check the current approved internal registry/policy if supplied; do not update it. Identify applicable AI-law questions from verified jurisdictions and organization role.
3. Apply source-defined triage dimensions: purpose, impact/stakes, data, human control, transparency, vendor dependencies and known red lines.
4. Choose a conditional internal route such as proceed-to-review, assessment-needed, restricted pending facts, or stop-and-escalate; do not present this as a legal risk tier unless verified.
5. List required controls, evidence, review owner and cross-functional tasks. Return an update proposal if the system is not inventoried.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve AI governance reviewer use-case branch

## Same-task addition: use-case fact map

For an internal AI use case, collect purpose, users, affected groups, data inputs/outputs, decision influence, human role, vendor/model, geography, lifecycle stage, and expected scale. Separate owner facts from vendor/source assertions and unknowns. Map only verified jurisdiction and organizational roles to current applicable authority and supplied internal policy; return review questions and owner actions. Use route labels such as `assessment-needed` or `restricted-pending-facts` as internal workflow states only, never as statutory risk classifications or numeric scores.
