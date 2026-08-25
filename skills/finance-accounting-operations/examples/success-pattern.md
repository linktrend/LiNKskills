# Example Trace: Read-Only Operations Brief

## Synthetic scenario

A redacted consumer snapshot covers one month, USD, a verified contract
`odoo-read-v1`, and declared read operations for invoices, payments, expenses,
budgets, cash flow, and period status.

## Trace

- The skill verifies the snapshot digest and preserves source references.
- It reports cash-flow base/downside assumptions, budget/actual variance,
  invoice/payment/expense ageing, close blockers, and runway risk.
- It labels the result as an observation, records an explicit approval request
  for any unresolved variance, and declares `external_calls: []` and
  `mutations: []`.
