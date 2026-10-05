# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `current_process_map`: current process map.
- `event_samples_and_time_window`: event samples and time window.
- `business_outcome_and_constraints`: business outcome and constraints.

## Completed output sections

- `bottleneck_evidence`: bottleneck evidence.
- `ranked_improvement_hypotheses`: ranked improvement hypotheses.
- `experiment_rollback_plan`: experiment/rollback plan.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
