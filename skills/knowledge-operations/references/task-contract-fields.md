# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `knowledge_inventory_and_audience`: knowledge inventory and audience.
- `owner_source_admission_metadata`: owner/source/admission metadata.
- `retrieval_and_freshness_evidence`: retrieval and freshness evidence.

## Completed output sections

- `knowledge_gap_and_ownership_register`: knowledge gap and ownership register.
- `freshness_retrieval_improvement_plan`: freshness/retrieval improvement plan.
- `librarian_intake_package`: Librarian intake package.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
