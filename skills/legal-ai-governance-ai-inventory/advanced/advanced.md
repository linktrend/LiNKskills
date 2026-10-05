# AI System Inventory and Role Record: active procedure

## Procedure

1. Establish whether the request is list, add, show, or propose an edit; read the supplied inventory and preserve stable system IDs.
2. For each system separately, record provider/deployer/importer/distributor role candidates and the evidence for each. Never assign a company-wide role.
3. Capture intended use, system boundary, data, affected people, geography, owner, lifecycle status and material changes; keep missing values explicitly unknown.
4. Separate inventory facts from derived risk classification or legal obligation mapping; route those to the relevant assessment task.
5. Draft inventory rows or an edit proposal with changes highlighted. No official registry write or obligation auto-derivation.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
