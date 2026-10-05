# Outside Counsel Invoice Compliance Review: active task method

## Trigger and required inputs

Review an outside-counsel invoice against supplied engagement terms and billing guidelines, producing line-item findings and an internal draft approval/rejection note.

Required typed fields: `invoice_and_lines`, `matter_and_firm`, `billing_guidelines`, `review_system`, `prior_invoice_evidence` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Reconcile invoice header, line items, hours, rates, expenses, tax and total arithmetically; identify currency, rounding, duplicate entries and missing detail before compliance analysis.
2. Read the approved engagement terms and billing guidelines. If absent, do not invent best-practice rules or mark a charge non-compliant; record “basis not supplied” and perform factual/arithmetical review only.
3. For each line item record date, timekeeper, role, task narrative, hours, rate, amount, guideline clause, evidence and status (supported, potential exception, unsupported, duplicate, needs clarification).
4. Screen for supplied rule categories such as block billing, prohibited administrative work, rate/staffing limits, vague descriptions, late submission, duplication and unapproved expense; distinguish rule breach from suspected pattern.
5. Recalculate any proposed reduction from explicitly supplied rates/amounts; show formula and source line. Do not use automatic “industry norm” caps or alter invoice records.
6. Draft an internal review/approval note or response text only when requested. Escalate disputed scope, potential privilege, budget exception, payment approval and systemic vendor issues to the named owner.
7. Return a line-by-line report with unresolved questions; never approve, reject, pay, communicate with outside counsel or update an e-billing system.

## Output contract

Return a JSON-compatible object with these fields: `invoice_reconciliation`, `line_item_findings`, `guideline_citations`, `draft_adjustment_summary`, `approval_note_draft`, `missing_evidence_and_escalations`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/invoice-review-compliance-scott-margetts/SKILL.md`
- Source entrypoint SHA-256: `16aeef7db279b02132d422da5cb6b0e536f5cd39b0a119cc6d1e40670f4ef21f`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/invoice-review-compliance-scott-margetts/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Every non-compliance flag cites a supplied guideline/term.
- [ ] Math ties to invoice line amount and rate.
- [ ] No payment or external rejection communication occurs.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
