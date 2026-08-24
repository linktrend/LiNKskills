# Old Patterns and Blacklist

- Treating a supplied Odoo snapshot as permission to call Odoo.
  - Resolution: require an exact approved contract and fail closed on unknown operations.
- Writing a private ledger or posting a journal entry from a reporting skill.
  - Resolution: return an evidence-labeled brief and identify the owning consumer.
- Calling a forecast a fact or hiding the downside assumptions.
  - Resolution: label observed values, assumptions, ranges, confidence, and unknowns separately.
- Marking an invoice, payment, expense, or period as final from a description-only match.
  - Resolution: require stable references, period, currency, and owner confirmation.
- Including live credentials, customer records, or company-private fixtures in evals.
  - Resolution: use synthetic or redacted consumer snapshots only and reject privacy violations.
- Treating a failed adapter, stale digest, or missing source as zero.
  - Resolution: preserve the missing state and set `PENDING_APPROVAL`.
