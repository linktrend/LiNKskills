# EU GPAI Code of Practice Alignment Review: active task method

## Trigger and required inputs

Compare an identified general-purpose AI model provider’s supplied practices or evidence against the current applicable EU GPAI Code of Practice or binding requirements.

Required typed fields: `model_and_provider`, `gpaI_status`, `code_version_and_signatory`, `evidence_set`, `authority_snapshot` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Confirm provider/model identity, EU-market connection, GPAI status, systemic-risk classification and whether the provider signed the Code. Do not infer these from a product label.
2. Retrieve the current official Code of Practice version and any current Commission or AI Office status statements. Record version, publication/adoption status, signatory list and as-of date.
3. Separate legally binding AI Act duties from voluntary Code commitments and from provider self-description. Do not convert a Code commitment into a statutory obligation.
4. For each applicable commitment, identify required artifact/evidence, scope, owner, reporting cadence and evidence supplied. Review documentation, copyright policy, training-data summary, safety/security and downstream information only within the model/provider role.
5. Compare evidence to each commitment. Classify evidenced, partial, missing, not applicable with basis or unknown; quote only short portions needed and preserve source pinpoint.
6. Identify gaps, dependency on confidential evidence, open questions and possible corrective actions. Avoid claiming “compliant” based only on public signatory status or template documents.
7. Return an alignment review for owner/counsel review; no self-attestation, Code submission or publication.

## Output contract

Return a JSON-compatible object with these fields: `scope_and_provider_gate`, `code_commitment_matrix`, `evidence_and_gap_findings`, `binding_law_vs_voluntary_code`, `remediation_options`, `legal_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/gpai-code-of-practice-compliance-werner-plutat/SKILL.md`
- Source entrypoint SHA-256: `ed1ac643924a3fb2b72deac98b0240b588320c7e4185b5e752ecdcebc4095cd4`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/gpai-code-of-practice-compliance-werner-plutat/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] Binding legal duties are separated from voluntary Code commitments.
- [ ] Current Code version and provider/signatory identity are verified.
- [ ] No compliance conclusion rests only on a signatory listing.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
