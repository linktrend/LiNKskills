# Vendor Legal and Compliance Due Diligence: active procedure

## Procedure

1. Confirm vendor identity, service criticality, data/system access and assessment stage; identify sources not available.
2. Run an initial evidence sufficiency screen before deeper diligence; label vendor assertions versus independently supported materials.
3. Review the source’s dimensions: security/privacy, regulatory/legal, financial, operational, continuity, subcontractors and concentration.
4. Compare evidence against approved requirements; do not treat certifications or questionnaire responses as proof beyond their scope/date.
5. For multiple vendors, compare against the same stated criteria and preserve tradeoffs; draft conditional recommendation only.
6. Propose mitigations, contract follow-up and monitoring triggers with owners. No approval, onboarding, vendor contact or system entry.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
