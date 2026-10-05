# Legal Litigation Oc Status — detailed task method

## Task method

1. Confirm scope, as-of date, selected matters, communication owner and approved counsel names/address source. If contact data is absent, use a role placeholder, not guessed recipient.
2. Read authorized matter/history and latest counsel report. State last update date and record coverage; do not imply current information when stale.
3. For each matter, draft targeted questions on posture, recent developments, next event, decisions, budget/fees, exposure and dependencies as supported. Avoid asking counsel for facts already present in supplied record.
4. Separate hard dates quoted from verified orders/contracts and legal calculations. Flag unresolved deadline basis for counsel; do not compute due dates or imply a deadline is valid.
5. Keep each matter request separate; exclude privileged internal strategy unless the owner specifically authorizes sharing and counsel confirms the distribution boundary.
6. Prepare a summary showing requested matters, skipped records and exact reason. Draft a user review checklist covering recipient, confidentiality, exact ask and approvals.
7. Return draft text only. Do not create Gmail drafts, email, calendar events, scheduled reminders or portfolio mutations.

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
