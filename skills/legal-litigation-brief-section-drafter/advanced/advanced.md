# Legal Litigation Brief Section Drafter — detailed task method

## Task method

1. Confirm written submission versus oral argument, section type, forum, filing posture, page/word limit source, case theory and review owner. If testimony in a witness voice is requested, stop that portion and provide prompts/checklist for the witness and counsel; do not compose recollection.
2. Use only supplied or authorized record materials. Build a fact-to-source map with exact pinpoints; preserve source-specific quotes verbatim only when the passage is open and exact. Paraphrase otherwise and mark the cite needed.
3. For each legal proposition, use an authority supplied or retrieved through a currently available approved research interface. Record source, jurisdiction, court, date and pinpoint. If not available, insert an explicit authority placeholder; do not reconstruct law from model memory or silently web-search.
4. Check that the requested section advances the stated theory, identify the strongest contrary record/authority, and disclose weak or unsupported points for counsel strategy. Separate advocacy framing from evidence.
5. Draft in supplied house style. Mark each unresolved factual assertion [VERIFY], each legal proposition [AUTHORITY VERIFY], and every missing pinpoint [CITE NEEDED]. Do not place internal drafting notes in purported filing text.
6. Run a complete citation inventory: compare each factual and legal proposition to its pinpoint, flag partial support, and report checked/unavailable counts. Deliver draft and reviewer notes as separate sections.
7. Return a draft only. Filing, service, signature, final authority check and professional responsibility remain with authorized counsel.

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
