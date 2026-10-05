# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `contracts_policies_official_source_records`: contracts/policies/official source records.
- `applicability_facts`: applicability facts.
- `period_and_reporting_audience`: period and reporting audience.

## Completed output sections

- `obligation_register`: obligation register.
- `evidence_and_exception_gaps`: evidence and exception gaps.
- `owner_deadline_review_brief`: owner/deadline review brief.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
