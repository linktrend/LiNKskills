# Regulatory Comment-Period Tracking and Decision Brief: active procedure

## Procedure

1. Read only the supplied authorized comment tracker and current official docket/source material. Record the date checked, open source gaps, proposal status and verified deadline/time zone.
2. Produce the source-shaped tracker view: deadlines within 14 days, other open comment periods, and recently decided items; include total open and undecided near-deadline counts only when the supplied snapshot supports them.
3. For each open item, summarize the proposal, affected operations, decision owner and deadline. Treat feed-watcher entries as discovery leads, not controlling legal sources.
4. For a decision-log request, prepare a proposal for filing / not-filing / waived only when an authorized attorney/owner direction and rationale are supplied. Do not make the filing decision or alter the tracker.
5. For a proposed filing decision, list public-record implications, possible adverse admissions/inconsistent positions, coordination concerns, deadline dependencies and counsel questions. Do not create a reminder or notification; offer a draft reminder plan only if requested.
6. Return a comment-period status brief, decision proposal, source coverage and unresolved owner/counsel questions. The source explicitly excludes comment-letter drafting; route that separate task to counsel. Never create a submission-ready comment letter, submit a filing, contact a regulator, or announce a position.

## Completion check

- Deadlines and statuses trace to current official source or are marked unverified.
- Filing decisions are proposals based on supplied authorized direction only.
- No tracker write, external notice, comment letter, filing or public position.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
