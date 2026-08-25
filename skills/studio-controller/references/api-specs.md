# Controller Review Interface

## Inputs

The controller accepts a bounded, synthetic or redacted observation set from a
consumer-owned adapter or `finance-accounting-operations`. Each item carries a
stable source reference, period, currency, amount/status, provenance, and
confidence. The controller does not read Odoo, Supabase, Vault, or any network.

## Review outputs

- variance and unmatched-item table;
- close checklist with evidence and owner;
- cash/runway assumptions and risk labels;
- approval-boundary result (`NOT_REQUIRED`, `PENDING_APPROVAL`, `DENIED`); and
- exact provenance and empty external-effects declaration.

The output is a review artifact, never a journal, ledger, accounting system,
period lock, approval, tax statement, or statutory/audit conclusion.

## Reuse boundary

`finance-accounting-operations` owns Odoo contract metadata and the finance
family workflow. `studio-controller` contributes only review, variance, close,
and escalation logic. The old Supabase `lsl_finance` integration is retired
from this primitive; rollback to that prior release is `studio-controller@v1.0.0`
if the staged v1.1.0 migration is not accepted.
