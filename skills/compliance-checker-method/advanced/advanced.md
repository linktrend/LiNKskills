# Compliance Checker Method: active procedure

## Procedure

1. Scope the supplied code/configuration/documentation or business process; identify included and excluded systems, data flows, jurisdictions and frameworks. Do not assume every named regulation applies.
2. Inventory the data categories and lifecycle from entry through processing, storage, sharing, retention and deletion. Preserve source paths/locations and distinguish observed evidence from owner assertions.
3. Review the source-defined areas: sensitive-data handling, retention, encryption, access control, audit logging, consent/rights handling and transfers. Use only supplied readable evidence; do not run scanners or source scripts.
4. Map each finding to a current primary requirement only when the governing framework and scope are verified; otherwise label the mapping candidate/unverified. Separate compliant, partial, absent, unknown and out-of-scope states.
5. Prioritize supported gaps with impact basis, evidence needed, owner role and proposed remediation. Do not certify compliance or promise an audit result.
6. Return a reviewable findings report, source locations, assumptions and counsel/control-owner questions; leave actions and system changes empty.

## Source-specific seven-category review

For an in-scope codebase or business-process source, review each category separately and record positive evidence as well as missing controls:

1. Personal/sensitive-data handling and data inventory.
2. Data retention, lifecycle and deletion/backup behavior.
3. Encryption at rest/in transit and key/secrets handling.
4. Authentication, authorization and access review.
5. Audit logging and monitoring.
6. Consent, preference and purpose enforcement.
7. Cross-border transfers, vendors and subprocessors.

The source names GDPR, HIPAA, SOC 2, CCPA and PCI-DSS. If the requester gives no framework focus, screen those as candidates from the supplied data, territory, business and role facts; none is assumed to apply. Record exact file/section/line evidence, production-vs-test context and review limitations. The preserved scan patterns and report schema are reference material only; automated scanners/scripts are not a Sara tool. Include framework scope, severity/status, remediation detail, cross-framework mappings and explicit `unable to assess` states as supported by evidence.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
