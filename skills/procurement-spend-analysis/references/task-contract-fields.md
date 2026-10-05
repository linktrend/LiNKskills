# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `authorized_spend_and_subscriptions`: authorized spend and subscriptions.
- `supplier_category_definitions`: supplier/category definitions.
- `comparable_periods_currencies_and_constraints`: comparable periods, currencies and constraints.

## Completed output sections

- `reconciled_category_spend_analysis`: reconciled category spend analysis.
- `optimization_options`: optimization options.
- `business_case_and_decision_requirements`: business case and decision requirements.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
