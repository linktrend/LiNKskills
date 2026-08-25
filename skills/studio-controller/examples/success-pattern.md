# Example Trace: Controller Review

## Scenario

A finance operations skill supplies a redacted monthly snapshot with a
currency, source references, and one documented variance.

## Trace

- Controller labels observations and assumptions, checks the variance, and
  prepares a close checklist.
- It returns the owner, confidence, and evidence reference for the unresolved
  item.
- It declares `external_calls: []` and `mutations: []`; no ledger or source
  record is created.
