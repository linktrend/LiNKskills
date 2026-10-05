# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `current_state_and_proposed_change`: current state and proposed change.
- `affected_services_processes`: affected services/processes.
- `impact_dependencies_and_owner`: impact, dependencies and owner.
- `approval_authority_and_constraints`: approval authority and constraints.

## Completed output sections

- `change_request`: change request.
- `impact_and_dependency_assessment`: impact and dependency assessment.
- `acceptance_rollback_plan`: acceptance/rollback plan.
- `decision_register`: decision register.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
