# Legal Litigation Matter Intake — detailed task method

## Task method

1. Capture how the matter arose, reporting person, date received, immediate source and confidentiality. Keep raw sensitive narratives minimized; reference source IDs.
2. Identify all known parties, aliases, parents/subsidiaries, witnesses, counsel and related matters. Do not claim a conflicts check was completed unless an authorized conflicts owner returned a result.
3. Record jurisdiction/forum and procedural dates only as documented; distinguish filed/served dates from a user estimate. Request prompt counsel review for apparent court, subpoena, regulator or response dates without calculating a deadline.
4. Capture issue, requested outcome, business impact, known documents, likely custodians and existing counsel. Label risk/materiality as provisional and use only owner-supplied scale.
5. Flag possible preservation, insurance, regulatory, employment, privacy or safety dependencies for counsel; do not issue a hold or contact parties.
6. List outside counsel status and engagement conflicts for owner completion. If conflicts remain unknown, mark the matter not cleared and route to authorized check before substantive work.
7. Return an intake draft and explicit approval/registration questions. No official matter creation, file setup, status update or legal hold action occurs.

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
