# Privacy Impact Assessment Draft: active procedure

## Procedure

1. Determine whether the requested assessment is a company PIA, jurisdiction-specific DPIA or another impact review; do not conflate them.
2. Check internal triggers and current legal mandatory-assessment criteria for each applicable jurisdiction using current primary sources.
3. Document purposes, data flow, roles, subjects, scale, retention, recipients, transfers and affected people from supplied facts.
4. Assess necessity, proportionality, alternatives and impacts across privacy, security, fairness, safety and rights; cite the factual basis.
5. Map safeguards and residual risk, assign owners, identify consultation/escalation triggers and monitoring evidence.
6. Return a draft with unresolved assumptions and counsel/privacy-owner decisions; no approval, launch or regulator consultation.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve GDPR compliance reviewer impact-assessment branch

## Same-task addition: impact assessment fact map

For the described processing, map context, purpose, people/data subjects, data categories, sources, recipients, systems, scale, retention, transfers, roles, necessity, proportionality, alternatives, plausible impacts, mitigations, residual questions, and accountable owners. Distinguish an internal privacy impact assessment from any jurisdiction-specific statutory DPIA or other assessment; apply a legal trigger only after current primary-source verification and confirmed organizational facts. Use the map to make unresolved evidence visible, not to infer approval or launch readiness.
