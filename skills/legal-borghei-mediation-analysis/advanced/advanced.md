# Mediation Strategy and Settlement Analysis: active procedure

## Procedure

1. Identify parties, claims, defenses, forum, procedural stage, mediation purpose and decision-makers; note missing/contested facts.
2. Separate legal exposure, evidence strength, damages assumptions, cost/time, insurance, business relationship and nonmonetary interests.
3. Map each side’s stated and inferred interests; label inferences and generate options that could address them without assuming acceptance.
4. Calculate settlement scenarios only from supplied assumptions, show sensitivity and avoid presenting an unsupported precise value as expected outcome.
5. Compare walk-away/BATNA and alternatives only when provided; preserve authority limits and strongest contrary case.
6. Prepare a confidential handling-aware draft mediation brief and questions for counsel. No offer, concession, filing or communication.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
