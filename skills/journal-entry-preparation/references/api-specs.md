# Native interface and data contract

## Inputs

- Required inputs: Entry type/period, affected GL/subledger, calculation support, accounting basis and reviewer., Entry type and period, trial balance, subledger/source schedules and affected balances., Approved accrual policy, entity/period, source-basis refs, posted amount already booked, account mapping
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: Balanced proposed entry with debit/credit, calculation, evidence, and review notes., Draft debit/credit entry, memo, support and audit trace., Accrual schedule with calculation support and balanced draft entries; no posting
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
