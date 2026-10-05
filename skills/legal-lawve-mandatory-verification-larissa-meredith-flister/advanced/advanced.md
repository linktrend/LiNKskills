# Legal Proposition and Citation Verification: active task method

## Trigger and required inputs

Verify whether a supplied legal proposition is supported by the cited authority and whether that authority is current for a specified jurisdiction and date.

Required typed fields: `propositions`, `citations`, `jurisdiction_and_date`, `primary_source_access`, `document_context` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Split the supplied draft into discrete legal propositions. Mark propositions that are factual, normative, procedural, statistical or interpretive and identify the authority needed.
2. Locate each supplied authority in an official or otherwise authoritative source; verify title, court/issuer, date, exact provision, status, amendments and jurisdiction.
3. Read enough surrounding text to test scope, definitions, exceptions, procedural posture and negative/limiting language. Confirm the cited passage actually supports the proposition, not merely mentions the topic.
4. Check currentness as of the requested date. Distinguish controlling, persuasive, superseded, amended, proposed, withdrawn and not-found sources.
5. Return claim-by-claim status (supported, partially supported, contradicted, outdated, citation mismatch, not verified) with pinpoint and concise reason. Preserve disagreement and uncertainty.
6. Suggest wording only when a source supports it; otherwise mark the claim for research or counsel. Do not represent source search as a legal opinion or silently edit the underlying official draft.

## Output contract

Return a JSON-compatible object with these fields: `claim_to_authority_table`, `support_and_scope_findings`, `currentness_and_status`, `citation_corrections_or_gaps`, `unverified_claims`, `reviewer_next_steps`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/mandatory-verification-larissa-meredith-flister/SKILL.md`
- Source entrypoint SHA-256: `ec5b342602a12f974be9464385830f4d3f669ed51a59602840a21b0f778a8ea4`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/mandatory-verification-larissa-meredith-flister/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Each proposition is independently checked against source text.
- [ ] Currentness and jurisdiction are stated.
- [ ] No citation is invented or validated from title/snippet alone.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
