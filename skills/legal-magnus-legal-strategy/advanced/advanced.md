# Counsel Issue-Spotting and Strategy Brief: active procedure

## Procedure

1. Turn the broad question into a bounded decision, identify affected business objective, domains, decision deadline and accountable owner.
2. Select only relevant source reference areas; the upstream broad legal-strategy library is issue-spotting methodology, not current law or authority.
3. Map facts, plausible legal/regulatory issues, IP/contract/privacy/employment/governance implications, alternatives, dependencies and strongest contrary interpretation.
4. Assess options against the owner’s stated objectives, reversibility, cost, time and exposure. Keep unknown jurisdiction/current authority explicit.
5. Route deep domain analysis to the relevant dedicated task and identify counsel questions for novel or high-impact conclusions.
6. Return a decision brief with options and evidence links; no legal advice, implementation or external action.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
