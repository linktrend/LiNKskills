# Native interface and data contract

## Inputs

- Personal taxpayer reference; request and decision question; jurisdictions and tax year/dates; option facts and authorized personal source references; current primary-authority citations/effective dates; reviewer role.
- Reads remain limited to specified records, period and scenario. Official authorities must be current and applicable to actual facts when the task runs.

## Outputs

- Draft option comparison worksheet with sourced facts/rules, calculations where supported, assumptions, sensitivities, missing facts and CPA/tax counsel questions.
- No tax-return filing, election, transaction, trade, contribution, donation, payment or source-system mutation.

## Abstract template tools

`read_file` maps to authorized native/document read; `write_file` maps to the task-owned draft artifact; `get_tool_details` maps to the currently supplied native schema/owner toolcard, not a callable tool. Do not assume Odoo or any personal-finance connector.
