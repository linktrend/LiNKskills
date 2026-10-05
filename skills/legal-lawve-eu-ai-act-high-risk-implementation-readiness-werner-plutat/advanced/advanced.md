# EU AI Act High-Risk Implementation Readiness: active task method

## Trigger and required inputs

Build an evidence-based implementation readiness plan after a named AI system has been classified as high-risk or classification is explicitly marked unresolved.

Required typed fields: `system_and_version`, `actor_roles`, `classification_record`, `implementation_evidence`, `authority_snapshot` and `scope_and_as_of`. Preserve unknown values explicitly.

## Procedure

1. Confirm system identity/version, intended purpose, deployment context and actor roles. Treat classification as a separate prerequisite; if uncertain, list that gate and do not assume the readiness obligations apply.
2. Retrieve current official EU AI Act text, amendments, effective/transition provisions and Commission guidance; record versions and dates. Supersede all dated claims in archived source material.
3. Create separate provider/deployer/other-actor matrices. Map each potentially applicable obligation to exact article/annex, trigger, current effective date, responsible owner and required evidence.
4. Review evidence for risk management, data governance, technical documentation, logging, transparency/instructions, human oversight, accuracy/robustness/cybersecurity, QMS, conformity path, registration and post-market monitoring only where current scope supports it.
5. Assess existing evidence—not intentions—against each requirement. Classify demonstrated, partial, missing, not applicable with basis, or unresolved; identify stale documents and contradictory controls.
6. Prioritize a sequenced readiness plan with dependencies, owner, evidence artifact and decision date. Keep legal interpretation and conformity-assessment decisions for qualified counsel/notified-body owners.
7. Do not claim RED/AMBER/GREEN or compliance unless a defined approved rubric and evidence support it; no filing, registration or policy/system changes occur.

## Output contract

Return a JSON-compatible object with these fields: `scope_and_role_gate`, `obligation_evidence_matrix`, `readiness_gaps`, `sequenced_action_plan`, `owners_and_dependencies`, `legal_questions`. Each material conclusion includes an evidence source and pinpoint; distinguish observed fact, requestor assertion, inference, proposal and unknown.

## Tool and checkpoint map

Read only authorized known paths using native `read`; write only the requested draft using native `write`/`edit`. Inspect live native schemas and owner toolcards; do not call abstract names. No source script is run. For Lisa, native agent SQLite checkpoint/history is authoritative; `.workdir/.../state.jsonl` is a portable path declaration, not runtime sidecar storage.

## Full source method and applicability

The full original skill folder, every supporting file, license notice and source manifest are preserved byte-for-byte under `references/upstream/`. Consult the exact entrypoint and named supporting references for task method detail. Do not inherit source permissions, tools, dates, legal rules, scorecards, company facts or jurisdiction. The source's license notices are retained and no license clearance is claimed.

- Source identity: `lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/eu-ai-act-high-risk-implementation-readiness-werner-plutat/SKILL.md`
- Source entrypoint SHA-256: `61705bf9e7422c461915705102b8e69e9f2391a3429d79a0f5ddd3f17d2ce8fd`
- Source folder: `references/upstream/lawve-ai-awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290/source/skills/eu-ai-act-high-risk-implementation-readiness-werner-plutat/`
- Full file hashes: `references/upstream/SOURCE-MANIFEST.json`

## Completion checks

- [ ] High-risk classification and actor role are recorded as evidence or left unresolved.
- [ ] Every legal duty has current official source, effective date and entity role.
- [ ] Readiness plan distinguishes missing evidence from noncompliance.
- [ ] Current legal authority and date are verified, or the specific proposition is explicitly unverified.
- [ ] No external effect or source-system mutation was performed.
- [ ] Draft and uncertified status is visible.
