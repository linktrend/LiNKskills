# French Legal Research and Authority Memo: active task method

## Trigger and required inputs

Prepare a source-grounded research memo on a defined question of French law or EU law as relevant to a France-based legal question. Other source modes route to their distinct contract, proofreading, document-review or legal-monitoring tasks.

Required typed fields: `research_question`, `facts_and_purpose`, `jurisdiction_scope`, `as_of_and_recency`, `available_sources` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Narrow the request to one issue or a small linked set. Identify decision, audience, relevant dates and material facts; list outcome-changing unknowns without delaying separable research.
2. Build a proposition list before research. For each proposition, identify the source class needed (current statute, regulation, official guidance, judgment or secondary commentary). Never create a citation from memory.
3. Search for and read the primary source; verify that the cited text supports the exact proposition and is in force on the stated date. Capture title, article/paragraph, court/date or official source reference, language and access date.
4. Separate French domestic law, EU law, treaty/international material and commentary. Explain hierarchy, territorial scope and conflicts only where sources support them; do not silently substitute a neighboring regime.
5. Analyze the verified rule against each fact, present plausible counterarguments and distinguish confirmed fact, user assertion, inference and legal uncertainty.
6. Return a concise memo plus an authority matrix. If official text or currentness is unavailable, mark that proposition unverified and state what authority would resolve it; refer material legal conclusions to qualified counsel.

## Output contract

Return a JSON-compatible object with these fields: `question_and_scope`, `authority_matrix`, `analysis_by_subissue`, `counterarguments_and_gaps`, `qualified_conclusion_and_next_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/assistant-juridique-christophe-quezel-ambrunaz/SKILL.md`
- Source entrypoint SHA-256: `701e6af15e62d9c09b71e5b029aa9498d98fb57e03e6280619aa31fca2da038d`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/assistant-juridique-christophe-quezel-ambrunaz/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Every legal proposition has a primary source and pinpoint or is explicitly unverified.
- [ ] A citation is checked for content support and current status.
- [ ] No specific advice, jurisdiction or case fact is invented.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
