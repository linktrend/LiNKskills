# Advanced incident and continuity guidance

## Prospective risk register

A prospective risk register is separate from incident intake and closure. Preserve cause, event, consequence, likelihood/impact statements, control evidence, and residual statement as owner-supplied material with row-level `evidence_refs` that resolve to supplied evidence. Those references establish traceability, not truth or support quality. If evidence does not substantiate a claim, retain the gap instead of promoting it to fact.

Use only the accountable owner's supplied rating scale and tolerance for ratings or acceptance thresholds. Caller-advisory inherent ratings, and owner-supplied ratings without an evidenced scale, must be `Unknown:` followed by a nonempty reason. A `Rating: <label>` is accepted only from an owner when the scale reference resolves to supplied evidence. Keep missing scale/tolerance, likelihood, impact, inherent rating, and residual rating explicitly unknown; an unknown rating does not suppress a separately labeled, evidence-bounded qualitative advisory rationale, treatment proposal, or review trigger. Preserve whether optional assessment text is a caller advisory proposal or owner-supplied, and label it unverified. Keep the unknown-rating gap when display prefixes identify its source. Do not calculate probabilities, losses, scores, or control effectiveness. Identify duplicate cause/event/consequence rows for owner resolution; never merge different ownership or silently select one. Distinguish designed controls from owner-reported operation and evidence; neither status alone proves effectiveness. Treatment and review timing may be proposed for owner consideration, but risk acceptance and control activation remain owner decisions.

## Evidence and ownership

Keep incident observations separate from hypotheses. Name the owning responder,
Platform, Program Ledger, and deployment authority even when a reference is
`not_reported`. A skill review can preserve evidence and prepare options; it
cannot assign authority or change an owning system.

## Recovery and continuity

Backup, restore, rollback, isolation, and failover are options with tradeoffs,
not actions. Require evidence for availability, recovery point, recovery time,
dependency, and residual risk. Never infer that a backup is restorable or that
a recovery is complete from a narrative.

## Communication and closure

Internal and customer messages may be drafted with audience and evidence, but
they remain unsent. Closure needs evidence capture, residual risks, owner
review, and a proposed or supplied state. An incident marked closed without
closure evidence stays uncertain and is not presented as complete.
