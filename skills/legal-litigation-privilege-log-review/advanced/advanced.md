# Legal Litigation Privilege Log Review — detailed task method

## Task method

1. Confirm log/protocol versions, review purpose and access authorization. Do not load privileged content into unrelated contexts or telemetry.
2. Check required fields and formatting against the supplied order/protocol: date, author, recipient, document type, subject description, basis and redaction/attachment relationships as applicable.
3. Review each entry only to the level authorized. Use metadata and approved doc refs; if content review is not authorized or needed, do not open the document.
4. Classify proposed disposition as facially complete/consistent, apparent issue, or attorney review. Record factual indicators, not a final privilege conclusion; privilege depends on governing law and context.
5. Check near-duplicates, repeated descriptions, blanket categories, inconsistent dates/participants, withheld attachments, mixed-purpose documents and missing family entries. Avoid inferring intent from a pattern.
6. Flag potential waiver, common-interest, work-product, redaction and confidentiality questions for counsel, using minimized excerpts/IDs.
7. Return QA table and attorney queue; do not amend the log, redact, produce, claw back or communicate with the other side.

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
