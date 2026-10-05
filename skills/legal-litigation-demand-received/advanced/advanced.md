# Legal Litigation Demand Received — detailed task method

## Task method

1. Confirm the document reference, recipient entity and receipt metadata. Preserve the original as supplied; do not alter, forward, acknowledge or share it.
2. Extract sender, claims, demanded conduct/payment, cited authority/contract, stated response date, attachments, delivery instructions and threats. Separate allegations from verified records.
3. Cross-check only authorized portfolio/document references. A similar name or subject is a possible match, not a confirmed related matter.
4. Build deadline table with “stated on face,” “contract/source says,” and “counsel-verified calculation” separated. If service, response period or legal deadline is unclear, escalate immediately and make no calendar computation.
5. Identify preservation, insurance notice, counterparty, regulatory or parallel matter questions only as possible issues; do not send notice or open/change records.
6. Offer bounded response paths (counsel review, factual investigation, contract/coverage review, request more context), with consequences and unresolved facts rather than a legal merits score unsupported by law.
7. Return a triage draft and urgent counsel questions. Handoff to matter-intake or demand-intake only as proposed next task; no contact, settlement or response is initiated.

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
