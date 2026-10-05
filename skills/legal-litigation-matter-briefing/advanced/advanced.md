# Legal Litigation Matter Briefing — detailed task method

## Task method

1. Confirm exact matter and authorized records; record an as-of date. Read current matter summary, history, latest owner reports and relevant source documents only.
2. Compare recorded status with new evidence. List actual changes by source/date and distinguish logged fact, counsel assessment, stale field and inference.
3. Extract upcoming dates with source and type. Keep dates printed in court/contract documents separate from calculated deadlines; no computation without verified current rule and counsel review.
4. Restate the case posture, key disputed issues, next event, outside-counsel status, exposure estimate only when sourced, preservation status and dependencies. Do not invent a risk rating or assert materiality totals.
5. Flag stale update time, missing acknowledgements, contradictory records, unavailable documents and decisions needed before next event.
6. Ask whether the existing risk/materiality field remains accurate; provide evidence/questions rather than editing the official record or changing reserves.
7. Return a concise counsel-ready briefing with source refs, facts/inferences separated, and decision owner.

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
