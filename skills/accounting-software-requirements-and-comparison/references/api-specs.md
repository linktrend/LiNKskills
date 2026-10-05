# Native interface and data contract

## Inputs

- Required inputs: accounting software selection, accounting and erp software comparison, vendor demo evaluation sheet, accounting package quotation tracker, three year software cost comparison, Also use it when the user describes a scored evaluation of shortlisted accounting, packages before one is chosen, or the same process happening in a spreadsheet, a document, or someone inboxes.
- Every read is bounded by the user-specified entity, period, object type and output scope.
- Odoo native read calls when available: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`; use only fields/arguments in the current supplied schema.

## Outputs

- Expected outputs: Follow the shared execution contract. The module-specific rules below define only domain fields, decisions, calculations, and safety constraints., ### Step 1 - Identify intent, Read the request and pick the intent before asking anything., "set up" or "build" or "create" -> the user wants artifacts; go to Step 2., "compare" or "which one should we pick" -> the user wants an evaluation; capture the shortlist, then Step 2., "our process is ..." or "it is in a sheet" -> the user wants to move an existing evaluation; capture it, then Step 2., "is this right" or "review" or "audit" -> the user wants a check, not a build; answer from what they share., "report" or "how do I ..." -> advice question; answer directly and offer the build only if it helps.
- Draft write: only a task-owned artifact using the current native `write` route. No write to Odoo, accounting ledger, payment rail, tax authority, email/customer or production config.
- Evidence references must be stable authorized source refs, not copied private data.

## Abstract template tools

`read_file` maps to authorized native read capability; `write_file` maps to a draft artifact; `get_tool_details` maps to the current supplied native schema and owner toolcard, not a callable tool.
