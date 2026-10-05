# Native interface map

- `read_file` maps to current native `read` on known authorized paths.
- `write_file` maps to native `write`/`edit` only for the requested draft artifact.
- `get_tool_details` means inspect current native schema and owner toolcard; no callable alias.
- `linkskills_use` and `linkbrain_read` only if exposed in the current native schema for that purpose.
- No shell, source scripts, legal database, external communication or business-system mutation is assumed.
