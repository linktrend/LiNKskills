# AI Vendor Contract and Governance Review: active procedure

## Procedure

1. Confirm the exact document set and whether it is an AI addendum, main agreement or Terms of Service; stop if required portions are missing.
2. Map provisions on training/reuse of inputs, confidentiality, output/IP, model changes, service/security, incident notice, audit, retention/deletion, subprocessors and liability.
3. Compare language with supplied approved positions and applicable privacy/security requirements. Do not invent company playbook positions.
4. For regulatory clauses, verify current law and actual role/transfer facts; label legal conclusions unverified if authority is unavailable.
5. Draft prioritized issues, fallback options and clause-specific proposed redlines for counsel. Do not negotiate, sign, accept terms or change vendor records.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.

## Same-task integration: Lawve AI governance reviewer vendor branch

## Same-task addition: AI vendor evidence collection

For a third-party model/vendor, build a vendor evidence table for model/provider, prompt and output handling, training/reuse, retention/deletion, subprocessors, security/incident evidence, audit evidence, change notices, human review, and contract terms. Mark each field `confirmed`, `source-asserted`, `missing`, or `conflicting`; request evidence where missing. Compare against a supplied policy/playbook only. Route contract language to the contract reviewer and privacy processing facts to the privacy task; do not turn this pack into an AI use-case or legal gap assessment.
