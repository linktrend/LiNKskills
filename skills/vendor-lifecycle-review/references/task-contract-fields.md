# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `vendor_purpose_criticality_and_candidate_requirements`: vendor purpose, criticality and candidate requirements.
- `contract_pricing_evidence_and_any_independently_prepared_performance_review`: contract/pricing evidence and any independently prepared performance review.
- `review_horizon_as_of_date_and_decision_authority`: review horizon, as-of date and decision authority.

## Completed output sections

- `supplier_diligence_and_selection_comparison`: supplier diligence and selection comparison.
- `renewal_exit_decision_options_and_notice_window_assessment`: renewal/exit decision options and notice-window assessment.
- `questions_and_approval_package`: questions and approval package.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
