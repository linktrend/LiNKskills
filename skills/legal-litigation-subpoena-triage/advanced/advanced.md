# Legal Litigation Subpoena Triage — detailed task method

## Task method

1. Confirm exact instrument and attachments, recipient, service method/date and internal receipt. Preserve original evidence; do not acknowledge service or contact issuer.
2. Classify only from its text and issuing authority (e.g. subpoena, civil investigative demand, grand-jury process). If grand-jury or criminal process is indicated, stop substantive triage and immediately route exact document to qualified counsel.
3. Extract command, requested materials/testimony, date range, place, return date, issuing court/agency and stated objection/response instructions. Distinguish text on face from legal effect.
4. Record deadlines as stated and service metadata; do not calculate the legal response or objection deadline without current primary authority and counsel verification. Flag apparent near dates for immediate escalation.
5. Cross-check authorized portfolio records and preservation status. Identify possible related matter/hold; do not initiate or release a hold.
6. Assess collection burden from supplied source locations and custodians. Identify privilege, privacy, confidentiality, trade secret, jurisdiction and scope questions; do not decide objections or produce documents.
7. Prepare a counsel-reviewed response-workstream plan with owners, evidence sources, dependencies and uncertainty. Do not draft/send objections, negotiate scope, certify completeness or make a production.
8. Return urgent triage, exact counsel questions and record gaps. No calendar/mail/drive/log updates occur.

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
