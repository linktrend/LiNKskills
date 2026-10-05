# Native interface and data contract

## Inputs

- Required inputs: Dated financial baseline, stage and supporting records, Requested CFO deliverable and audience, Documented assumptions/decision question, Dated financial baseline and stage, Requested deliverable/audience and known assumptions, Relevant cash, revenue, costs, headcount or financing records
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: Requested CFO model/analysis with explicit assumptions, Cash/runway/unit economics/fundraising/board draft as applicable, CFO financial model/analysis, runway or unit economics, Board/fundraising package draft where requested
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
