# Native interface and data contract

## Inputs

- Required inputs: financial-statements-from-financial-statement-generation, cash-position-and-runway, budget-vs-actual-comparison, forecast-accuracy-data, department-head-updates, prior-board-minutes, cap-table-and-fundraising-status
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: complete-board-deck, executive-summary, supporting-appendix-financials, pre-read-email, post-meeting-minutes-template
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
