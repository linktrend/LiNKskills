# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `specific_scenario_and_service_owner`: specific scenario and service owner.
- `safe_observed_interfaces`: safe observed interfaces.
- `response_authority`: response authority.
- `success_and_rollback_conditions`: success and rollback conditions.

## Completed output sections

- `response_runbook`: response runbook.
- `decision_and_escalation_tree`: decision and escalation tree.
- `simulation_readiness_record`: simulation/readiness record.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
