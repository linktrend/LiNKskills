# Moroccan E-commerce Site Compliance Evidence Audit: active task method

## Trigger and required inputs

Audit a supplied Moroccan e-commerce website capture for privacy and consumer disclosure evidence, subject to current local-law verification.

Required typed fields: `site_and_capture`, `operator_and_market`, `privacy_evidence`, `consumer_terms_evidence`, `authority_snapshot` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Confirm a website-based Morocco e-commerce flow and whether the operator is a marketplace, seller or informal social-media shop. If scope differs from the source method, identify the gap rather than forcing its checklist.
2. Review the whole supplied capture: homepage, navigation/footer, product page, checkout, terms, privacy notice, cookies/consent and contact/complaint path. Record URL, language, capture date and unavailable pages.
3. Retrieve current official Moroccan legal texts and regulator guidance; check amendment, implementing measures, effective status and any current authority procedure. Do not rely on source-era periods or old template conclusions.
4. Create separate privacy and consumer-disclosure checklists. For each item record exact visible evidence, source URL/pinpoint, status (present, partial, absent in reviewed capture, unclear, not in scope), rule source/date and required confirmation.
5. Check checkout and consent flow only from direct supplied observations; distinguish site content from actual backend processing or consent logging which the capture cannot prove.
6. Classify an item “absent” only if the relevant pages/flow were fully reviewed; otherwise use “not observed/needs client confirmation.” Avoid turning an incomplete capture into a legal finding.
7. Return prioritized correction suggestions and local counsel questions. Do not contact CNDP, consumers, payment provider, or change/publish the website.

## Output contract

Return a JSON-compatible object with these fields: `site_and_market_scope`, `page_and_evidence_inventory`, `privacy_findings`, `consumer_disclosure_findings`, `authority_and_date_matrix`, `gaps_and_counsel_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/morocco-ecommerce-compliance-audit-omar-laftouh/SKILL.md`
- Source entrypoint SHA-256: `1a3e7bbc236711da5f95b608cdea7362f4d5341492a144e8a103526ec71cdb43`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/morocco-ecommerce-compliance-audit-omar-laftouh/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Page coverage and original language are recorded.
- [ ] Current Moroccan primary sources support legal findings.
- [ ] Not observed is distinct from confirmed absent.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
