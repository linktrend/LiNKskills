# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `approved_goals_and_constraints`: approved goals and constraints.
- `executive_program_owner_plans`: executive/Program owner plans.
- `capacity_risks_and_dependencies`: capacity, risks and dependencies.
- `planning_horizon`: planning horizon.

## Completed output sections

- `four_week_quarter_year_operating_plan`: four-week/quarter/year operating plan.
- `ownership_and_dependency_map`: ownership and dependency map.
- `review_decision_dashboard`: review/decision dashboard.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
