# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `evaluation_decision_and_risk`: evaluation decision and risk.
- `candidate_baseline_identities_and_comparable_run_settings`: candidate/baseline identities and comparable run settings.
- `authorized_immutable_cases_and_provenance`: authorized immutable cases and provenance.
- `task_trajectory_side_effect_contracts`: task/trajectory/side-effect contracts.
- `observed_results_and_approved_cost_budget`: observed results and approved cost budget.

## Completed output sections

- `versioned_evaluation_plan_and_dataset_manifest`: versioned evaluation plan and dataset manifest.
- `grader_specification_and_observable_assertions`: grader specification and observable assertions.
- `per_case_and_per_dimension_comparison_with_uncertainty`: per-case and per-dimension comparison with uncertainty.
- `regression_and_blocked_environment_report`: regression and blocked-environment report.
- `owner_decision_gaps_and_redacted_monitoring_plan`: owner decision, gaps and redacted monitoring plan.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
