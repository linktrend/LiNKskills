# Advanced Controller Review Logic

## Reconciliation Strategy

- Match by stable source reference, period, currency, and amount. A similar
  description is not enough to merge observations.
- Segment unresolved variances by source quality and preserve unmatched lines.
- Keep observed values, inferred values, assumptions, and unknowns distinct.

## Controller Escalation

- If a mismatch is material, the snapshot is stale, or support is missing,
  halt completion and request the owning consumer or Principal's review.
- Preserve source references and an explanation for every excluded or
  conflicting observation; never alter the source record.
- A close checklist is preparation only and cannot declare a period locked or
  legally/statutorily closed.
