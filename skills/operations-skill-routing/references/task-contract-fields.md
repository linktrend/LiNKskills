# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `request_and_intended_decision_output`: request and intended decision/output.
- `scope_audience_and_available_evidence`: scope, audience and available evidence.

## Completed output sections

- `selected_task_skill_and_reason`: selected task skill and reason.
- `required_input_dependency_list`: required input/dependency list.
- `owner_and_handoff`: owner and handoff.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
