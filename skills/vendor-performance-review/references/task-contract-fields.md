# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `existing_vendor_catalog_and_internal_owners`: existing vendor catalog and internal owners.
- `approved_score_weights_anchors_and_criticality_context`: approved score weights/anchors and criticality context.
- `signed_sla_targets_credit_terms_deadlines_caps`: signed SLA targets, credit terms/deadlines/caps.
- `observed_period_reliability_support_security_evidence`: observed period reliability/support/security evidence.
- `as_of_date_and_prior_period_records`: as-of date and prior period records.

## Completed output sections

- `vendor_performance_scorecard_with_evidence_and_uncertainty`: vendor performance scorecard with evidence and uncertainty.
- `sla_trend_and_contract_based_credit_claim_draft`: SLA trend and contract-based credit-claim draft.
- `third_party_risk_matrix_and_mitigation_priorities`: third-party risk matrix and mitigation priorities.
- `keep_review_replace_recommendations_and_accountable_follow_ups`: keep/review/replace recommendations and accountable follow-ups.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
