# Legal Litigation Claim Chart — detailed task method

## Task method

1. Confirm patent versus civil chart and the requested submode. Require exact asserted claim/cause/defense and side; do not infer which theory applies.
2. Load the controlling element text from the supplied order/authority and preserve version/date. If the chart depends on current law or claim construction not provided, identify the gap and do not invent an element or construction.
3. Decompose each claim into individual limitations without paraphrase loss; for dependent claims preserve all incorporated limitations. For civil claims, keep the element list tied to supplied governing authority and jurisdiction.
4. Map each limitation independently to the target evidence with exact pinpoints; quote only source text actually reviewed. Classify supports / contradicts / absent / unclear, and note alternative explanations and source coverage.
5. For patent infringement/invalidity modes, keep technical mapping separate from legal conclusions such as infringement, anticipation, obviousness, equivalents, divided performance or intent; flag each as counsel analysis. Treat any supplied claim-construction ruling as source text, not an invitation to add a new construction.
6. For an existing chart, audit every row, cite and gap instead of accepting its conclusions. Neutralize spreadsheet formula-leading values before output if a table file is requested; do not execute cells or formulas.
7. Prioritize the missing proof and disputed evidence. Return a draft chart and question list, not a verdict or filing-ready contention.

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
