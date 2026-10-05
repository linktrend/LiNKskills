# Legal Litigation Matter Update — detailed task method

## Task method

1. Confirm matter ID exists in authorized supplied records, current status and as-of date. Do not create a substitute record if it is missing.
2. Capture event type/date, when reported, who supplied it, concise facts and exact source. Separate event date from entry date.
3. Compare requested status/risk/deadline/materiality/authority changes to the current record. Do not silently overwrite; show before/after, source and decision owner.
4. For risk, settlement authority or legal dates, require the owner’s explicit basis. Do not infer a new risk level, authority or deadline from a summary.
5. Preserve append-only chronology: correct errors with a dated correction note rather than erasing prior entries, if the owner’s record policy permits.
6. Identify related tasks such as briefing, hold review or counsel update as proposals only. Do not send or update the official record.
7. Return the entry and diff for the authorized matter owner to apply and read back.

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
