# Native interface and data contract

## Inputs

- Required inputs: cash by account and availability status; revenue/AR dated receipt forecast; AP, payroll, tax and debt-service dated disbursements; budget and relevant scenario assumptions. Read approved related task artifacts when present: `accounts-receivable-and-collections`, `accounts-payable-review`, `revenue-forecast`, `operating-budget-preparation`, and `tax-obligation-calendar-and-status`. Missing one component blocks only the related lines or resulting cash conclusion.
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: 13-week-cash-forecast-table-markdown-or-csv, scenario-comparison-base-bear-upside, zero-cash-date-and-runway-projection
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
