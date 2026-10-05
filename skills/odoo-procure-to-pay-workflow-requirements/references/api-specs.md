# Native interface and data contract

## Inputs

- Required inputs: Setting up the purchase flow for a new Odoo instance., Implementing purchase order approval workflows (2-level approval)., Configuring vendor price lists with quantity-based discounts., Troubleshooting billing/receipt mismatches in 3-way matching.
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: 1. **Activate**: Mention `@odoo-purchase-workflow` and describe your purchasing scenario., 2. **Configure**: Receive exact Odoo menu paths and field-by-field configuration., 3. **Troubleshoot**: Describe a billing or receiving issue and get a root cause diagnosis.
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
