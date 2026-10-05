# Legal Topic or Incident Brief: active procedure

## Procedure

1. Select daily, topic or incident mode and define audience, time window, event/topic and requested decisions.
2. Search only authorized supplied records; list source categories unavailable rather than assuming access to email, chat, calendar or CLM.
3. For incident mode, build a sourced timeline and identify potentially relevant agreements/policies; avoid determining notification duties or privilege without current authority/counsel.
4. Synthesize facts, prior positions, current state, key considerations, gaps and next-step questions. Distinguish record evidence from inference.
5. Return a concise brief for review. Do not contact people, set meetings, update matters or make legal decisions.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
