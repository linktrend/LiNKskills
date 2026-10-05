# EU AI Act Fundamental Rights Impact Assessment: active task method

## Trigger and required inputs

Screen or draft a Fundamental Rights Impact Assessment for a specified high-risk AI deployment where Article 27 applicability may arise.

Required typed fields: `system_and_classification`, `deployer_status`, `deployment_context`, `rights_and_risk_evidence`, `authority_snapshot` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Confirm the system’s high-risk classification and actual use context; if not verified, stop the FRIA merits and route to classification first.
2. Read current official Article 27 and related provisions, amendments and guidance. Record the exact deployer gate, Annex III point, exception and effective status; do not rely on the archived source’s dates.
3. Test each scope gate from evidence: public-law body/private public-service provider or the specified creditworthiness/insurance use; separately check applicable exceptions. Unknown is not “in scope” or “out of scope.”
4. Map deployment purpose, duration/frequency, affected groups, likely harms to fundamental rights, foreseeable misuse, human decision points, safeguards and complaint/remedy paths.
5. Cross-reference an existing DPIA or risk assessment only where supplied. Avoid duplicate data-protection analysis; identify differences and missing rights-impact content.
6. Assess residual risk and proposed mitigations with evidence, responsible owner and timeline. Distinguish rights analysis, legal applicability, stakeholder consultation and operational recommendation.
7. Return the structured draft and qualified questions for counsel/affected-stakeholder input. Do not notify an authority or represent the assessment as complete/legally sufficient.

## Output contract

Return a JSON-compatible object with these fields: `applicability_gates`, `deployment_and_affected_group_map`, `rights_risk_matrix`, `safeguards_and_residual_risk`, `DPIA_cross_reference`, `notification_or_counsel_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/fundamental-rights-impact-assessment-eu-ai-act-art-27-werner-plutat/SKILL.md`
- Source entrypoint SHA-256: `ac592b39ca0025de853319a9db803a3c04be6fede4a9374a3defdf0d7cf15cef`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/fundamental-rights-impact-assessment-eu-ai-act-art-27-werner-plutat/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] High-risk and deployer gates are tested before substantive assessment.
- [ ] Affected people/groups and rights impacts are specific to deployment facts.
- [ ] No universal Article 27 duty or current date is asserted.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
