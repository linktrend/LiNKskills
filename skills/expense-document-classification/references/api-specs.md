# Native interface and data contract

## Inputs

- Required inputs: expense register, petty expense sheet, expense book with tax, bill and voucher log, expenses booked to the right account, Also use it when the user describes the same process happening in a spreadsheet, on paper,, or in someone's inbox., Do not use it for: payroll calculation, tax filing, tax-return preparation, legal advice,
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: Follow the shared execution contract. The module-specific rules below define only domain fields, decisions, calculations, and safety constraints., ### Step 1 - Identify intent, Read the request and pick the intent before asking anything., "set up" / "build" / "create" -> a new structure; go to Step 2., "our expenses are in a sheet" / "we currently record ..." -> capture the existing, process first, then Step 2., "is this right" / "review this" / "audit this" -> a check, not a build; answer from what, they share and do not rebuild.
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
