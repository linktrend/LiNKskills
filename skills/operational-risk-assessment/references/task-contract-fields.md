# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `activity_scope_and_dependencies`: activity scope and dependencies.
- `risk_evidence_and_business_impact`: risk evidence and business impact.
- `existing_controls_and_risk_authority`: existing controls and risk authority.

## Completed output sections

- `risk_register`: risk register.
- `control_evidence_assessment`: control/evidence assessment.
- `treatment_and_monitoring_proposals`: treatment and monitoring proposals.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
