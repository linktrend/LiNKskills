# Task method: privacy policy drafting

## Intake schema

- `business_identity_and_contact` — Confirmed controller/entity identity, address and privacy contact/DPO status; unknowns remain placeholders.
- `product_and_user_journeys` — Website/app/service type, account/transaction flows, audiences, features and relevant vendors.
- `user_geographies_and_jurisdictions` — Where users are located/targeted, entity locations and actual territorial connections, supported by evidence.
- `data_categories_and_sources` — Data categories, people, collection/source, sensitivity and whether children are in scope.
- `purposes_and_basis_evidence` — Each processing purpose and confirmed legal basis/operational evidence; never assign on behalf of the business.
- `vendors_and_transfers` — Processors/recipients, data locations, transfer routes and actual safeguards, if confirmed.
- `cookies_and_platform_tools` — Observed/supplied cookies, SDKs, analytics, advertising, AI and platform-contract disclosures.
- `retention_and_rights_processes` — Confirmed retention/deletion rules, rights channel, appeal/contact path and response owner.
- `approved_template` — Existing counsel-approved template or explicit choice to use a reference structure; template status and version.
- `review_mode` — Quick/batched or expert/detail review and requested policy language/output format.
- `authority_sources_and_as_of` — Current official primary legal sources, regulator guidance where appropriate, retrieval date and jurisdiction.

## Procedure

1. Select QUICK or EXPERT mode. Gather the request, audience, product/service type, business identity and user geographies in one concise intake; then ask only practice questions required by the supported jurisdiction set. No company facts are inferred from source examples or other skills.

2. Determine potentially applicable-law set before drafting: verify entity location, users’ locations/targeting, product/sector and processing facts. If jurisdiction is international or unknown, do not apply a “strictest common denominator” automatically; record candidate regimes and verify scope from current official sources or leave a visible gap.

3. Build a processing inventory by purpose: data categories and people, collection/source, system, purpose, recipient, retention, security statements, rights path and legal-basis evidence. Record who confirmed each operational representation and its source/date.

4. Verify current legal content using primary statutes/regulator sources and current platform terms for the selected jurisdictions. The copied 2026-06 source pack, CNIL materials and article references are research leads only; do not repeat their law, date, enforcement, fine or platform claims without current verification.

5. Choose the client’s/counsel’s approved template first. If none is supplied, offer the copied backbone as a structural starting point only after disclosure; preserve source wording only where counsel confirms it is suitable. Do not treat archived template clauses as legally reviewed for this matter.

6. Assemble only clauses supported by both (a) a verified applicable requirement or an explicitly selected, approved policy position and (b) confirmed actual practice. Leave `[GAP — confirm before publishing: …]` where facts are unknown. Do not include favorable claims about encryption, children, DPO, retention, opt-out, GPC/DNT or transfers unless directly confirmed.

7. Use a reader-first structure: identity/contact; data and source; purpose/basis; recipients/transfers; retention; rights/contact; cookies/platform/AI disclosures if evidenced; security/breach text only to verified practice and applicable law; effective date/change history. Keep employee/HR privacy notice separate.

8. Run citation firewall: identify every statute/section, fine, deadline and effective date in the draft and tie it to a current source/date. Reconcile every clause against the practice inventory and show removed or omitted claims, unresolved facts, conditional links and source gaps.

9. Flag specialist review for children, health/biometric, fintech, data sales/brokerage, AI training, large-scale monitoring, multi-regime coverage, uncertain transfers or other source-identified high-risk cases. Present a review-ready draft and issue list; do not publish, send, or represent it as legal advice.


## Required work product sections

- jurisdiction and applicability map
- confirmed-practices inventory
- modular privacy policy draft
- practice-to-clause reconciliation
- citation/currentness table
- visible gaps and founder questions
- counsel-review triggers and change log

## Quality checks

- [ ] Every representation in the policy maps to a confirmed practice or explicitly applicable current requirement.
- [ ] Jurisdiction and source currentness are reasoned before clause selection.
- [ ] All citations, dates, fines and legal claims trace to current authoritative sources.
- [ ] All unresolved facts remain visible as gaps; no unsupported privacy claim is made.
- [ ] The practice-to-clause reconciliation and change log are included.
- [ ] High-risk counsel triggers are surfaced without holding routine draft preparation.

## Source method checkpoints

The base source’s QUICK/EXPERT modes, jurisdiction-first law selection, modular clause assembly, 12-point self-QA/citation firewall, conditional links and practice-to-clause reconciliation are adapted above. Malik’s template-first gate and detailed processing inventory are added as intake and drafting checks. Full original methods and useful references remain intact under `references/upstream/`; no original law/version claim, connector instruction or permission is assumed.

## Native interfaces and persistence

Map `read_file` to native `read` on known approved paths and `write_file` to native `write`/`edit` for the requested artifact only. Inspect current schemas/toolcards rather than calling an abstract `get_tool_details`. Lisa’s native SQLite agent checkpoint is authoritative; the `.workdir` state path is portable metadata only.
