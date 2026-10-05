# Legal Litigation Deposition Prep — detailed task method

## Task method

1. Confirm witness identity/role, deposition posture, examiner role, scope/notice, forum, theory and authorized document set. Avoid personal-data collection not needed for preparation.
2. Inventory sources attributed to or mentioning the witness, with coverage limits and exact locators. If e-discovery is unavailable, work only from supplied exports and state the gap.
3. Identify topics that bear on approved disputed issues. For each, separate known record facts, witness knowledge hypothesis and counsel question; do not infer what witness remembers.
4. Build an outline in sections: background/scope, role and chronology, key documents, topic questions, adverse evidence, follow-up and exhibit order. Use neutral prompts that elicit actual testimony.
5. Flag inconsistent statements and possible impeachment by exact source comparison. Do not coach false testimony, suggest answers, suppress adverse material or create a witness narrative.
6. Where jurisdiction-specific witness-statement/deposition procedures matter, require counsel to check current rules. Do not make rule-based objections or deadlines without current authority.
7. Return the outline and source map as draft work product. Counsel decides strategy, privilege use, exhibit designation and examination.

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
