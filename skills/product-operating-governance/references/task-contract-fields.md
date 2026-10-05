# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `product_service_mandate_and_accountable_owner`: product/service mandate and accountable owner.
- `approved_priorities_and_operating_evidence`: approved priorities and operating evidence.
- `customer_financial_technical_dependencies`: customer/financial/technical dependencies.

## Completed output sections

- `ownership_and_decision_map`: ownership and decision map.
- `product_operating_review`: product operating review.
- `handoff_and_evidence_gaps`: handoff and evidence gaps.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
