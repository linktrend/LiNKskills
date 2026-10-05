# AI Regulation Gap Analysis: active procedure

## Procedure

1. Confirm organizational/regulatory footprint and system-specific provider/deployer roles; scope each regime by definitions, thresholds, sector and territorial nexus.
2. Research current operative primary law and official guidance before extracting duties. Record text version, dates, phase-ins and uncertainties; do not reuse hardcoded source-era tables as current law.
3. Extract requirements into actor/action/trigger/standard/evidence fields and distinguish legal duty, guidance, draft rule and voluntary framework.
4. Map each requirement to supplied control/document evidence; state absent, partial, unknown or not applicable with reason and confidence.
5. Prioritize by verified severity/time, dependencies and owner; keep any regulatory timeline unverified when not freshly sourced.
6. Return a gap analysis draft and research/counsel questions; no compliance certification or registry updates.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve AI governance reviewer regulation branch

## Same-task addition: sourced requirement-to-evidence matrix

For each current and applicable requirement, record jurisdiction, primary-source citation/version/date, responsible actor, action, trigger, standard, effective date if verified, and source type (binding law, official guidance, internal policy, or voluntary framework). Map only supplied control or document evidence to it, with owner and status `supported`, `partial`, `unknown`, or `not_applicable` plus reason. Keep applicability and effective-date questions open when the organization's role or footprint is not confirmed. Do not use a source-era scorecard or timeline as current law.
