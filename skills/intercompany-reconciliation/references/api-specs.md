# Native interface and data contract

## Inputs

- Required inputs: Two identified entities and their reciprocal accounts; shared cutoff/period and transaction scope; each side’s original transaction detail, currency and independent GL control total; supplied counterparty mapping, stable invoice/transfer references and matching tolerances. A common-currency view additionally needs a supplied exchange rate, date and source; absence must remain an explicit gap.
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: One reciprocal-entity workpaper: original books on both sides, reciprocal matched/unmatched transactions, independent source-total tie-outs, timing/FX/mapping/one-sided break classifications, aging, evidence-backed cause hypotheses and owner questions. No netting away differences, elimination entries or posting.
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
