# Legal Litigation Demand Draft — detailed task method

## Task method

1. Require a completed intake and confirm the intended recipient, requested relief, entity/counterparty and review owner. If material strategic fields are missing, finish separable drafting structure but mark dependent text needs-context.
2. Read underlying evidence and build a claim-to-source table. Preserve the intake’s uncertainties; do not make a demand amount, deadline or factual assertion more certain than its source.
3. Run a pre-draft issue check for privilege filters, possible admissions, settlement communication characterization, accord-and-satisfaction concerns, tone and distribution. Such labels do not themselves create legal protection; require forum-specific counsel review.
4. Use a supplied approved form/precedent if authorized. Otherwise create clearly marked draft prose with placeholders rather than borrowing a foreign jurisdiction form as controlling.
5. Every factual allegation gets a record source or [VERIFY]; every legal proposition gets a verified authority source or [CITE NEEDED]. Do not research through unavailable tools or fabricate citations. Flag thin research and stop that legal proposition.
6. Separate outgoing proposed letter text from internal review notes. Create a post-draft checklist; do not mark sign, send, service, filing, tender, approval or calendar actions complete.
7. Return the draft for qualified counsel review. A request to issue/send is outside this skill and requires the separate authorized human process.

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
