# Native interface and data contract

## Inputs

- Required inputs: current-banking-inventory-all-accounts-and-institutions, fee-statements-last-3-months, yield-data-on-deposits, credit-facility-terms-if-applicable, cash-forecast-from-cash-forecasting
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: banking-architecture-summary-with-recommendations, fee-analysis-with-negotiation-targets, yield-optimization-plan-and-fraud-prevention-checklist
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
