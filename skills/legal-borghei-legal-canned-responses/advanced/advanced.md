# Routine Legal Inquiry Response Drafting: active procedure

## Procedure

1. Classify inquiry and sub-type; if ambiguous, ask the minimal category question. Keep DSR, subpoena, hold issuance/release and regulated response details within the dedicated task pack where applicable.
2. Read only an approved template with metadata, use case, variables, escalation triggers and last review date. If absent, propose a template structure; do not present invented legal language as approved.
3. Run the source’s universal and category-specific escalation screen for litigation, regulator/government contact, criminal exposure, binding waiver, media, novel facts, cross-border conflicts and sensitive DSR/hold conditions.
4. If a trigger fires, stop routine drafting and prepare an escalation brief; any preliminary text must be marked for counsel review only.
5. Populate only supported variables, leave unknowns bracketed, verify jurisdiction/deadline with current authority and tune audience tone without changing approved legal positions.
6. Return draft, escalation result, variable checklist and follow-up proposal. Never send, sign, file, release a hold or update a tracker.

## Source-specific categories and escalation

Retain the source categories and subtypes as routing prompts: (1) data-subject requests (acknowledgment, verification, fulfillment, denial, extension); (2) discovery/litigation holds (initial notice, reminder, modification, release); (3) privacy inquiries; (4) vendor legal questions; (5) NDA requests; (6) subpoena/legal process; and (7) insurance notifications. The exact approved template, last-review date and every required variable must be supplied; otherwise draft with marked placeholders or stop for missing context.

Run universal escalation first for litigation/regulator/government contact, a binding commitment, criminal exposure, media attention, novel facts or conflicting jurisdictions. Apply category-specific escalation prompts for minor/sensitive-data requests, contested or overbroad holds, vendor dispute/negotiation, competitor/M&A NDAs and every subpoena/legal-process matter. When any trigger fires, stop templated response generation and route a clearly labeled counsel-review draft or escalation summary. Never state that the automated detector found every trigger.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve canned-response generator

## Same-task addition: template fit and lifecycle metadata

Before selecting text, classify the inquiry into the source categories (privacy/DSR, vendor, NDA, legal process, hold, insurance) and confirm the specific template's owner, version, last verification date, use conditions, required variables, and retirement status. Bind only variables supported by the request and authorized sources; leave unknown jurisdiction, deadline, contact, or policy bracketed. An expired or unverified template is a draft reference only: flag it and ask the template owner for a current approved version. Do not edit the template library. This adds a template-lifecycle check to the base pack's inquiry classification/escalation flow.
