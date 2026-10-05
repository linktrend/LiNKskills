# AI Governance Policy Starter Draft: active procedure

## Procedure

1. Interview for policy purpose, audience, systems, geography, actual workflows and accountable roles before drafting; do not invent governance bodies or controls.
2. Separate confirmed practice from proposed policy. Mark each proposed rule requiring an owner decision.
3. Research current official guidance only where requested and available; do not use a model-policy template as evidence that a rule is mandatory.
4. Draft modular sections covering scope/definitions, roles, approved-use lifecycle, risk review, data/security, human oversight, vendor use, incidents, monitoring, exceptions and training as supported by facts.
5. Include explicit placeholders for missing values, implementation owner and review cadence. No policy adoption, employee notice or publication.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
