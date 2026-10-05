# GDPR Audit Readiness Review: active procedure

## Procedure

1. Establish the processing operations, data-subject locations, entity roles and territory from evidence; determine scope only against current primary text and official guidance.
2. Review supplied records by source method areas: processing inventory, purpose/lawful basis, special-category conditions, rights handling, DPIA threshold/quality, processor terms, transfers, breach handling and retention.
3. For each area, record evidence, date, sample/population and status; keep legal conclusions, deadlines and exemption analysis conditional when authority or facts are missing.
4. Identify gaps, contradictory practices and dependencies across product, security, HR and vendor owners; do not turn checklist flags into a compliance certification.
5. Draft an audit-readiness matrix, priority questions, owner roles and remediation options; no regulator response, DSAR action or system updates.

## Source-specific six-question coverage

Retain six Article-focused sample prompts, with each legal criterion and period freshly verified: (1) Article 30 processing records and update status; (2) lawful basis by purpose and special-category conditions where relevant; (3) DPIA threshold, required elements and any prior-consultation issue; (4) rights-request handling and response timing; (5) transfer mechanisms and supporting assessment evidence; and (6) a complete personal-data-breach record, including notification analysis. Never lift the source's example windows or deadlines into a live conclusion without checking current primary text and facts.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
