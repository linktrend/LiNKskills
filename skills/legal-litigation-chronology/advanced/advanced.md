# Legal Litigation Chronology — detailed task method

## Task method

1. Confirm authorized matter or explicitly bounded document-only set, period, source coverage, use limits and prior version. For discovery/disclosed material, require the owner to confirm permitted use under the actual protective order and applicable rules; if unresolved, stop extraction from that set and list the missing authorization.
2. Choose a privilege posture from counsel-provided screening. If no screening exists, use a mixed/uncertain flagging posture; if the user requests abort, stop. Never make an authoritative privilege determination.
3. Read the identified sources and record source ID, document date, event date, custodian/author where present and precise locator. Report sources unavailable; never silently supplement from memory or public search.
4. Extract one event per independently supported fact, preserve contradictory dates/accounts as separate entries with linked source refs, and merge duplicates only when they describe the same event. Do not resolve factual disputes.
5. Keep timeline description factual and neutral. Distinguish inference, significance and legal characterization; do not compute limitations or procedural deadlines without current verified rules.
6. If a theory tag or statement-of-facts variant is requested, identify the supplied theory/side, label the framing provisional, exclude privilege-flagged items from external-facing variants unless counsel expressly clears them, and retain exact pinpoints.
7. Compare with the prior chronology, state additions/changes/removals and source coverage limitations, then return a draft for counsel review.

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

## Same-task integration: Lawve chronology builder

## Same-task addition: neutral event views

Maintain one neutral event set with source locator(s) on every event, then derive working, statement-of-facts, or witness-specific views as filters rather than rewriting facts. Tag significance only against a supplied party, theory, or pivot fact and include a short reason; do not infer a case theory or legal effect. Record counsel-supplied privilege posture; when none is supplied, flag entries for counsel review and exclude them from external-facing variants by default without declaring them privileged. Before using disclosed material, capture the proceedings identifier and permitted-use confirmation only when required by the actual forum's current verified rules or protective order. Never universalize a pinned UK rule.
