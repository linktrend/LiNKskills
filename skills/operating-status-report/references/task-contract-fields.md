# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `approved_plan_and_reporting_period`: approved plan and reporting period.
- `current_program_owner_status_evidence`: current Program-owner status/evidence.
- `dependencies_decisions_and_blockers`: dependencies, decisions and blockers.

## Completed output sections

- `operating_brief`: operating brief.
- `decision_action_exception_register`: decision/action/exception register.
- `next_checkpoint`: next checkpoint.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
