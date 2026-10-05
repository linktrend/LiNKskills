# Legal Litigation Portfolio Status — detailed task method

## Task method

1. Confirm authorized dataset, report scope and as-of date. Never enumerate records beyond the supplied scope.
2. Normalize only known status/risk/stage categories from owner definitions. Keep unknown/missing distinct; state denominator for each count.
3. Calculate date windows only from valid date inputs and supplied owner rules. Label `recorded due date` separately from `verified legal deadline`; do not infer deadline rules.
4. Identify overdue/stale/unassigned conditions based on explicit thresholds; if no threshold is supplied, report elapsed age and request owner interpretation rather than applying a hidden default.
5. Aggregate exposure/materiality only when same currency, basis and completeness are established; otherwise show ranges/buckets or mark not comparable.
6. List closed matters separately and flag active items with missing counsel, hold status or next action as data gaps, not automatic legal deficiencies.
7. Return read-only report with coverage, caveats, calculation basis and source record refs. No field updates, assignments, reminders or notices.

## Evidence and legal applicability

- Use the forum, governing document, legal authority, date and record only when supplied or verified by a current approved source.
- Keep jurisdiction-specific questions open when facts are absent. Do not generalize a rule from the pinned upstream material.
- Record exact source version, date and pinpoint; distinguish `verified`, `user-reported`, `proposed`, `conflicting`, `unknown`, and `not reviewed`.
- If authorized primary authority or approved native operation is unavailable, produce the separable draft and name the gap.


## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Failure recovery

On missing evidence, preserve unaffected work and name the source/owner needed. On conflicting records, retain both with dates. On unreadable/denied sources, report exact source and limitation; do not use memory or external-source fallback as if verified. On an ambiguous privilege, service, deadline, hold or legal determination, escalate to qualified counsel. On a failed authorized draft write, inspect its actual status before retry; no external effects or official matter mutations are allowed by this pack.
