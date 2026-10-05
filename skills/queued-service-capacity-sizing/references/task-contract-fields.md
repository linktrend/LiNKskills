# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `queue_class_and_observation_window`: queue class and observation window.
- `arrival_counts_timestamps_and_p50_p90_p99_demand`: arrival counts/timestamps and P50/P90/P99 demand.
- `service_duration_distribution_and_units`: service duration distribution and units.
- `concurrent_server_worker_counts_shrinkage_and_availability`: concurrent server/worker counts, shrinkage and availability.
- `waiting_time_service_objective_and_budget`: waiting-time service objective and budget.

## Completed output sections

- `queue_assumptions_and_input_quality_assessment`: queue assumptions and input-quality assessment.
- `arrival_service_utilization_model`: arrival/service/utilization model.
- `waiting_risk_and_capacity_scenarios`: waiting-risk and capacity scenarios.
- `ramp_availability_sequence_and_decision_package`: ramp/availability sequence and decision package.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
