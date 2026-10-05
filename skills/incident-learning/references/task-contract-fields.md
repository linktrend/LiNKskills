# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `incident_scope_and_timeline`: incident scope and timeline.
- `observations_and_retained_evidence`: observations and retained evidence.
- `existing_controls_and_prior_incidents`: existing controls and prior incidents.

## Completed output sections

- `fact_hypothesis_timeline`: fact/hypothesis timeline.
- `escape_and_contributing_factor_analysis`: escape and contributing-factor analysis.
- `corrective_regression_effectiveness_plan`: corrective/regression/effectiveness plan.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
