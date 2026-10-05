# Product Feature Legal Risk Assessment: active procedure

## Procedure

1. Define the feature, change, intended and foreseeable uses, users, data, markets, claims and decision impact.
2. Identify relevant legal/product domains from evidence: privacy, consumer protection, accessibility, IP, safety, AI, contracts and sector rules.
3. Apply only supplied internal calibration. Verify legal rules and scope by current primary sources; do not equate a score with a launch decision.
4. Assess severity, likelihood/evidence, reversibility and affected parties; identify strongest alternative interpretation and missing tests.
5. Draft mitigations, conditions, owners and handoffs to specialized review packs, preserving dependency on unresolved facts.
6. Return risk memo; no approval or launch blocking/unblocking claim.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
