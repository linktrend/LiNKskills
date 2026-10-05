# US Employment Law Research Brief: active task method

## Trigger and required inputs

Research one defined United States employment-law issue for specified federal, state and local jurisdictions and date.

Required typed fields: `topic_and_question`, `jurisdictions`, `time_window`, `facts_and_worker_groups`, `source_policy` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Lock the legal topic, exact jurisdictions, covered worker groups, research date and recency period. Do not default to all states/cities or assume a national survey.
2. Read the pack’s preserved source-policy guide. Use primary legal text for legal rules; label agency summaries and secondary commentary separately.
3. Research federal law first, then each named state, then city/county where the supplied facts establish local coverage. Record overlapping, conflicting and preempted rules as distinct issues.
4. For statutes, regulations, cases, agency actions and pending bills, record authority, effective/status date, jurisdiction, exact provision and retrieval date. A bill or proposal is not current law.
5. Apply each rule only to supplied facts. Mark employer size, worker type, location or timing gaps that change the result; do not infer compliance.
6. Provide a structured brief and comparison table with source links/pinpoints, distinction between primary and secondary sources, and any issue requiring licensed employment counsel.

## Output contract

Return a JSON-compatible object with these fields: `scope_and_jurisdictions`, `primary_authority_findings`, `secondary_source_context`, `comparison_table`, `effective_date_and_status`, `open_factual_or_legal_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/employment-law-research-yue-deng-wu/SKILL.md`
- Source entrypoint SHA-256: `d39b6c390f5fd5ad03c2219179cfa64d64709880cc325f986acc665ceee11ffb`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/employment-law-research-yue-deng-wu/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Only requested jurisdictions are researched.
- [ ] Pending bills and agency commentary are not described as enacted law.
- [ ] Primary and secondary authority are visibly separated.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
