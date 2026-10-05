# Regulatory Gap Register Status and Proposal: active procedure

## Procedure

1. Read only the supplied authorized register snapshot and its schema/version; establish the snapshot date and declared scope.
2. Produce status counts/buckets for open, in-progress, closed, risk-accepted, watch and comment-decision records as represented in the source; preserve source status and avoid interpreting unverified legal rules as overdue or binding.
3. For a requested close proposal, require resolution evidence and a stated rationale; for risk-acceptance proposal, require rationale, named authorized acceptor and review/revisit conditions.
4. Check owner, due/revisit dates, source freshness and verification state; flag missing or inconsistent values without changing records.
5. Return status report, proposed closure/acceptance records and owner/counsel questions. Do not ingest policy diffs, send notices, update tracker status or claim a full legal review.

## Completion check

- Every count and proposal traces to the supplied snapshot.
- `external_effects` and `mutations` are empty.
- Gap ingestion, dedupe and notice proposals route to `legal-regulatory-gap-surfacer`.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
