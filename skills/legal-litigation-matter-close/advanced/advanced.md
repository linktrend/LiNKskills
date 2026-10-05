# Legal Litigation Matter Close — detailed task method

## Task method

1. Confirm the exact matter and source proving the reported outcome; a verbal “done” alone is not proof that proceedings and obligations ended.
2. Capture disposition type, effective date, parties, terms that can be recorded, final cost/exposure basis and lessons. Mark sealed/confidential/privileged material for counsel-controlled handling.
3. Check remaining dependencies: appeal/reconsideration, payment/performance, releases, costs, insurance, related claims, regulator duties, settlement confidentiality, outstanding deadlines and connected matters.
4. Review legal-hold status only from supplied authorized records. Do not release, suspend, narrow or tell custodians to resume deletion; prepare a separate counsel question if release is being considered.
5. Propose closure status and archive checklist. Preserve required official books, order/settlement, correspondence, hold and destruction schedules according to supplied policy and counsel direction.
6. Keep active matter totals and portfolio calculations out of the closure decision unless their approved definitions are supplied.
7. Return a draft closure entry, remaining-action list and owner approvals. Do not delete, archive, update a matter log or mark closed in a source system.

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
