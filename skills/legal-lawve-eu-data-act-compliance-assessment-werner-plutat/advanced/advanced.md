# EU Data Act Scope and Obligation Assessment: active task method

## Trigger and required inputs

Assess a defined connected-product, related-service, data-sharing or data-processing service question under the EU Data Act.

Required typed fields: `product_or_service`, `actors_and_roles`, `data_and_access`, `request_or_contract`, `authority_snapshot` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Identify product/service, data generation, actors, requested access/use and decision date. Do not assume a connected product, related service or data holder from marketing labels.
2. Read the current EUR-Lex consolidated Regulation (EU) 2023/2854 and official Commission material. Record ELI/CELEX, consolidation date, relevant amendment and access date; verify transitional provisions.
3. Select only relevant branches: product-design/access, user/third-party sharing, B2B terms, exceptional public-sector access, cloud switching, interoperability, smart contracts or international access. Keep branch conclusions separate.
4. Map each actor’s role and each dataset’s status, including personal data, trade secrets and readily available data. Identify consent/legal basis and confidentiality constraints as separate evidence questions.
5. For each applicable article, record trigger, responsible actor, effective date, source text, current process/contract evidence, exception path and unresolved issue. Distinguish binding law, guidance and recommendation.
6. Compare supplied interface, contract or workflow to the verified obligations; propose clause/product/control changes as drafts only and flag national enforcement or interpretive questions.
7. Return an evidence-linked assessment and prioritized owner list. Do not make a data disclosure, contract change or authority response.

## Output contract

Return a JSON-compatible object with these fields: `scope_and_role_analysis`, `data_flow_and_request_map`, `article_by_article_obligation_matrix`, `contract_or_design_gaps`, `effective_date_questions`, `owner_actions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/eu-data-act-compliance-assessment-werner-plutat/SKILL.md`
- Source entrypoint SHA-256: `81d9364ab426d35414810a59b9234f6ed6e57d04cb1861c76ba6cd942a5653e9`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/eu-data-act-compliance-assessment-werner-plutat/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Data Act branch is selected from facts, not keywords.
- [ ] Article and effective-date claims are tied to current official text.
- [ ] Personal-data, trade-secret and data-holder questions stay explicit.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
