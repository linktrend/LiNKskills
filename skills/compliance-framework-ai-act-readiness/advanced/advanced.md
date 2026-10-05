# AI Act Readiness Assessment: active procedure

## Procedure

1. Establish the exact AI system, intended purpose, lifecycle role and territories from evidence; do not assume the organization is provider or deployer.
2. Check current primary EU AI Act text and official guidance for territorial/material scope, definitions, phase-in and amendments. Mark every legal classification/date unverified when no current source is available.
3. Apply the source method’s question set: system role/scope, risk category, prohibited-practice indicators, high-risk criteria, transparency duties, data governance, human oversight, documentation and incident handling.
4. For any potential high-risk path, map required conformity route and technical documentation only as a candidate checklist; do not imply a notified-body outcome or sign a declaration.
5. Separate statutory duties from voluntary standards and cross-framework reuse; link each candidate obligation to source evidence and owner role.
6. Deliver an assessment draft with unresolved facts, authority pinpoints, evidence gaps and counsel/technical-owner decisions; no registration, release or attestation.

## Source-specific forcing questions

Keep the original six-question structure as candidate issues to verify against current EU primary text before use:

1. Article 5 prohibited-practice indicators and any express exceptions.
2. Article 6/Annex III high-risk routes and any conditional carve-out.
3. Article 43 conformity-assessment route and applicable annex/module.
4. Article 25 organization role and resulting role-specific duties.
5. Article 50 transparency duties across interaction, synthetic content and relevant biometric/emotion/deepfake cases.
6. Articles 51–55 GPAI status, systemic-risk criteria and provider duties.

Do not use source-era thresholds, implementation dates or role assumptions as current law; cite a freshly checked authority or mark unresolved.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
