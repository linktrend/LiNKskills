# Native interface and data contract

## Inputs

- Required inputs: Setting up a new Odoo instance for a company for the first time., Configuring multi-currency or multi-company accounting., Troubleshooting tax calculation or fiscal position mapping errors., Creating payment terms for installment billing (e.g., Net 30, 50% upfront).
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: 1. **Activate**: Mention `@odoo-accounting-setup` and describe your accounting scenario., 2. **Configure**: Receive step-by-step Odoo menu navigation with exact field values., 3. **Validate**: Get a checklist to verify your setup is complete and correct.
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
