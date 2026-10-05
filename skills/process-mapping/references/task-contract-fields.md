# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `trigger_and_finished_outcome`: trigger and finished outcome.
- `actors_events_and_authorized_records`: actors, events and authorized records.
- `sample_population_and_observation_window`: sample population and observation window.

## Completed output sections

- `as_is_process_map`: as-is process map.
- `handoff_raci_and_exception_table`: handoff/RACI and exception table.
- `timing_evidence_gaps`: timing/evidence gaps.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
