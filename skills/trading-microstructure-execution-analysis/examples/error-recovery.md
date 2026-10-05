# Error recovery — trading-microstructure-execution-analysis

If a task-critical identifier, timestamp, unit, sign, denominator, cost input or source record is missing or contradictory:

1. Preserve the supplied facts and record the exact conflict.
2. Mark only affected findings `unknown`, `not_assessed`, or `partial`; do not fill missing values with zero.
3. Continue independent calculations only when they cannot be mistaken for the blocked conclusion.
4. Name the exact field, why it changes the decision, and its owner. Technical contract gaps route to Eric; legal/accounting/tax gaps route to Sara.
5. Retain any strategy recommendation as conditional and advisory; no execution or approval follows from this report.

Do not write a recovery JSONL sidecar. Reference existing native session and Program Ledger state. This pattern is not an evaluation pass.
