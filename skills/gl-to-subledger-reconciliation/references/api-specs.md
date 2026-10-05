# Native interface and data contract

## Inputs

- Required inputs: One reporting entity, one GL control account, cutoff/period and currency/units; same-cutoff GL and subledger detail with source control totals and stable IDs; supplied account mapping and matching tolerances (otherwise exact match).
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: One GL-to-subledger workpaper: original source values, normalized keys in separate fields, matched/unmatched records, independent source-total tie-outs, aged breaks, evidence-backed cause hypotheses and owner questions. Bank reconciliation, reciprocal-entity reconciliation and posting are separate tasks.
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
