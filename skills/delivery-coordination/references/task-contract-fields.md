# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `approved_technical_prd_and_execution_plan`: approved technical PRD and execution plan.
- `module_phase_issue_dependencies`: Module/Phase/Issue dependencies.
- `executor_and_integration_evidence`: executor and integration evidence.

## Completed output sections

- `delivery_status_and_blockers`: delivery status and blockers.
- `dependency_owner_handoffs`: dependency/owner handoffs.
- `acceptance_and_release_evidence_gaps`: acceptance and release evidence gaps.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
