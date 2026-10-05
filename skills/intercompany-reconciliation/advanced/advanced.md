# Intercompany reconciliation

Reconcile reciprocal due-to/due-from detail between one defined entity pair, period and transaction scope. Bank work routes to `bank-reconciliation`; GL-to-subledger work to `gl-to-subledger-reconciliation`; elimination/posting is separate.

Inputs: both entities’ reciprocal detail; approved counterparty map; shared transaction references; transaction currency; supplied reporting/local currency rate with date/source; each GL control total.

1. Fix both entity IDs, accounts, cutoff, currencies and totals independently; preserve original values.
2. Match reciprocal entity, invoice/transfer ID and transaction amount/currency; mark fuzzy candidates.
3. Classify cutoff/timing, FX, mapping, unapplied payment, disputed, duplicate and one-sided items; cause remains a sourced hypothesis.
4. Show both original books; create common-currency view only with supplied rate/date/source.
5. Tie each side’s matched plus unmatched records to its own GL total; report reciprocal break, aging, evidence and owner questions.
6. Return supported follow-up candidates; never net away a difference or fabricate/post elimination.

Acceptance: pair, accounts, period, currencies, original values and both totals visible. No invented FX rate, policy or cause; no ledger mutation, payment, filing or external communication.