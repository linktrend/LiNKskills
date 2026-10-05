# Legal Litigation Demand Intake — detailed task method

## Task method

1. Prefill only from authorized records and answers. Ask the matter owner to confirm party identity and entity; do not infer the sender from a company name alone.
2. Capture event timeline, evidence references, contract sections, governing-law clause, prior outreach, desired outcome and fallback. Keep allegation, admission and verified fact distinct.
3. Record response/deadline dates only with their source. Separate dates printed in a demand or contract from a calculated legal deadline; do not choose default response periods.
4. Ask for per-matter posture: tone, response window, settlement communication marking, signer and distribution. Leave blank/unresolved if no informed answer; do not substitute a practice-wide default.
5. When materiality or the owner requests depth, gather leverage/BATNA, downside tolerance, insurance/counterparty risks and privilege filters. User may defer; record omissions rather than fabricate answers.
6. Identify jurisdiction, forum and as-of date only when law-related questions depend on them. Put unsupported legal issues in a counsel-question list.
7. Return the completed intake as a draft for owner review, with a precise handoff to the separate demand-draft task; do not create/send any letter.

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
