# Advanced operating logic

All examples use synthetic references such as `supplier-demo-001` and
`contract-demo-001`. No source body is copied into a release.

## Supplier comparison and claim verification

Normalize supplier identity, category, scope, quote or price basis, currency, effective
date, service assumptions, source reference, and confidence. A comparison may report
`match`, `gap`, `unclear`, or `not_applicable`; it never selects a supplier. A price
claim is `confirmed` only when the supplied source identifies its basis and date.
Conflicting or stale claims become `needs-evidence` and name the owner question.

## Contract, renewal, and performance tracking

Extract only supplied obligations, notice windows, renewal rules, service levels,
responsible owners, dependencies, and review dates. Mark missing dates and ambiguous
terms `not_reported` or `unknown`; do not infer enforceability. Performance tracking is
a watchlist from supplied measures, incidents, and owner observations, not a score that
automatically changes a contract or supplier status.

## Concentration and continuity risk

Assess dependency count, substitution evidence, lead-time exposure, geographic or
service concentration, recovery assumptions, and unresolved owner actions. Risk is
`low`, `medium`, `high`, or `unknown` only when the supplied signals support that label.
High or unknown material risk routes to a consumer owner with an approval brief and no
automatic failover, purchase, termination, or communication.

## Approval briefs

An approval brief states the decision requested, alternatives considered, evidence
references, assumptions, cost/pricing basis, risks, owner, expiry, and next human action.
It does not approve spending, accept terms, create an order, or authorize credentials.
Requests to approve, order, accept, negotiate, renew, terminate, send, or mutate are
pending and fail closed when the action is undeclared.

## Failure, privacy, and audit

Reject live-looking material before parsing or echoing. Classify unavailable,
malformed, unauthorized, ambiguous, and privacy-rejected evidence separately. Retry
only idempotent local preparation once. Emit `FAILED` or `PENDING_APPROVAL` with safe
next action, evidence references, idempotency key, and exact rollback. Never fall back
to guessed supplier state.
