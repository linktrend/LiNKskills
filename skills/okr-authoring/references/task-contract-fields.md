# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `approved_business_objective`: approved business objective.
- `baseline_outcome_evidence`: baseline/outcome evidence.
- `owner_horizon_and_constraints`: owner, horizon and constraints.

## Completed output sections

- `objective_and_key_result_draft`: objective and key-result draft.
- `measurement_definitions`: measurement definitions.
- `initiatives_and_dependency_map`: initiatives and dependency map.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
