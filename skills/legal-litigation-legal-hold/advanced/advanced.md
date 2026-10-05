# Legal Litigation Legal Hold — detailed task method

## Task method

1. Classify request as issue-draft, refresh-draft, release-proposal or status. Confirm the matter is authorized for review and identify qualified counsel. If the underlying matter/conflicts status is unknown, prepare only a neutral intake checklist and escalate; do not issue or label a hold active.
2. Collect facts about dispute/investigation, potentially relevant data, date range, custodians, systems, retention settings and known deletions from supplied/authorized evidence. Distinguish a proposed custodian/scope from an approved one.
3. Identify the actual jurisdiction, forum, preservation source and as-of date needed for legal conclusions. If missing, do not state that a duty has attached, that a deadline applies, or that a scope is legally sufficient; create precise counsel questions.
4. For issue-draft, propose a narrowly described preservation scope, systems, custodian instructions, acknowledgement method, contact owner and exception process. Do not use broad boilerplate as a company fact or say “the law requires” without verified current authority.
5. For refresh-draft, compare current scope/custodians/systems against prior notice and records; flag new/departed custodians and unverified preservation actions. Keep proposed updates distinct from acknowledgements actually received.
6. For release-proposal, require written counsel/authorized-owner direction, disposition of appeals/related claims/regulatory duties, retention instructions and affected hold count. Treat release as a proposal only; never instruct deletion or normal-retention resumption.
7. For status, report only the authorized records supplied: issued/status fields, last confirmed refresh, next owner-approved review date, acknowledgements and gaps. Do not infer active coverage or calculate a universal six-month interval.
8. Return notice/refresh/release drafts with conspicuous “DRAFT — DO NOT DISTRIBUTE” and counsel-review gate, plus an unexecuted operational checklist. No email, calendar, HR/IT/drive action, legal_hold field update, actual issuance or release is performed.

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
