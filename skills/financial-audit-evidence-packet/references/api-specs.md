# Native interface and data contract

## Inputs

- Required inputs: year-end-trial-balance, all-bank-and-investment-statements, ar-and-ap-aging-summaries, payroll-register-and-tax-filings, cap-table-and-equity-documents, fixed-asset-register, legal-agreements-and-contracts
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: audit-readiness-assessment, complete-pbc-list-with-status, organized-audit-binder, walkthrough-documentation-package, open-items-tracker
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
