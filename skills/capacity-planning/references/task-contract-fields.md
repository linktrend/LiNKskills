# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `demand_units_and_horizon`: demand units and horizon.
- `available_capacity_and_units`: available capacity and units.
- `observed_throughput_backlog_and_quota_limits`: observed throughput, backlog and quota limits.
- `service_expectations_and_budget`: service expectations and budget.

## Completed output sections

- `demand_capacity_table`: demand/capacity table.
- `bottleneck_and_uncertainty_register`: bottleneck and uncertainty register.
- `base_constrained_and_expansion_scenarios`: base, constrained and expansion scenarios.
- `decision_and_monitoring_plan`: decision and monitoring plan.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
