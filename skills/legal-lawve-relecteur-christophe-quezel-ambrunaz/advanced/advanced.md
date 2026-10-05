# French-Language Document Proofreading: active task method

## Trigger and required inputs

Proofread a supplied French document for grammar, spelling, syntax and register while preserving meaning, citations and defined terms.

Required typed fields: `document_text_or_ref`, `audience_and_register`, `editing_scope`, `protected_terms`, `output_mode` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Confirm language variety, audience, document version and whether the request is proofreading or broader rewriting. Preserve author voice and all legal meaning unless editing scope expressly includes style suggestions.
2. Read the full supplied text in context. Identify spelling, agreement, grammar, syntax, punctuation, typography and register issues; do not comment on correct passages unless a summary is requested.
3. For each correction provide a locator, short original excerpt, proposed correction and category. Distinguish objective correction from optional style improvement.
4. Treat citations, quotations, defined terms, party names, numbers and legal propositions as protected. Flag apparent inconsistencies or citations for separate verification rather than silently changing substance.
5. Check edits for agreement, cross-reference integrity, heading/numbering consistency and accidental change in legal or factual meaning. If a source document cannot be written safely, return a reversible change table.
6. Return the requested correction artifact. If no issue is found, state that concisely without claiming the document is legally correct or factually verified.

## Output contract

Return a JSON-compatible object with these fields: `document_identity_and_scope`, `correction_table`, `meaning_sensitive_queries`, `style_suggestions_if_requested`, `unchanged_content_checks`, `completion_note`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/relecteur-christophe-quezel-ambrunaz/SKILL.md`
- Source entrypoint SHA-256: `2c7d373f9015e2791faef1adf82e17ee0ecc18158845b679efc1ed1516337c48`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/relecteur-christophe-quezel-ambrunaz/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Objective corrections are distinct from optional style choices.
- [ ] Citations and legal meaning are not silently changed.
- [ ] Every suggested change has a locator and proposed form.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
