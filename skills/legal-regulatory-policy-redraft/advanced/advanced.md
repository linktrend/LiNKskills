# Policy Redraft Proposal from Verified Requirement: active procedure

## Procedure

1. Require current approved policy and a separately verified rule/gap; otherwise stop rule-dependent drafting and present the exact missing source.
2. Confirm organization/product role and applicable scope; distinguish binding text from guidance and internal choice.
3. Draft only affected sections in redline/replace format, with [verify] markers for authority-dependent text and placeholders for unknown operations.
4. Check consistency with adjacent policies, actual practices, cross-references, defined terms and owner responsibilities.
5. Explain each proposed change, its source, implementation dependency and alternative wording.
6. Return draft to policy owner/counsel. Do not alter, approve, issue or publish the policy.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
