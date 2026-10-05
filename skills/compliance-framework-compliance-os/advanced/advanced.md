# Multi-Framework Compliance Program Orchestration: active procedure

## Task boundary

This pack owns the standing multi-framework operating model: portfolio scope, common-control/evidence architecture, recurring mock-audit cadence, annual program calendar, owner capacity and backlog. It does not assess readiness for a single named audit window or certification milestone; route that request to `compliance-framework-compliance-readiness`.

## Procedure

1. Confirm the request is for a standing or annual multi-framework program. If it names a specific audit window/certification stage and asks whether supplied evidence is ready, route to `compliance-framework-compliance-readiness`.
2. Gather organization profile and candidate frameworks. Verify legal applicability separately from contractual demand, voluntary standard adoption and certification goals.
3. For each candidate, create an applicability decision record with exact source, threshold/fact, role, confidence and unresolved owner question. Do not infer obligations from industry labels.
4. Map control statements to common evidence only where objectives, populations, time windows and quality criteria match; preserve framework-specific gaps and lower-confidence mappings.
5. Consolidate evidence inventory by artifact, owner, source, period, freshness and approved access route; flag unowned, stale or unverified evidence.
6. Design a mock-audit sample plan per chosen framework and scope; do not run source simulators or claim an audit result.
7. Sequence work by verified obligations, external commitments, dependencies, audit capacity and evidence reuse. Draft the backlog/calendar and mark all certification decisions for owners.

## Completion check

- Every material fact and legal/regulatory proposition has an authorized source, exact location and date, or is marked unverified/unknown.
- Task-specific output conforms to `references/schemas.json#/definitions/output`; questions and applicability limits remain explicit.
- `external_effects` and `mutations` are empty. This is a draft workflow, not legal, semantic, runtime or audit certification.

## Completion and partial-work contract

Return `completed_draft` only when each substantive required section listed in `references/task-contract-shape-fixture.json` contains task-specific content and the output cites at least one supplied evidence reference. An empty object, heading-only field or unsupported placeholder is not a completed deliverable.

When a material input or authority is missing, return `needs_context`, record the exact field/source and reason in `work_product.missing_inputs`, preserve unknown/conflicting facts in `work_product.unknown_facts`, and record independent work in `work_product.partial_work`. Complete unaffected work where possible; never invent facts to make the contract appear complete. The schema allows task deliverable fields to remain empty under `needs_context`.
