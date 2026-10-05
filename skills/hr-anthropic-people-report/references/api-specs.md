# Supported consumer interface mapping

| Canonical metadata label | Supported interpretation | Limits |
|---|---|---|
| `read_file` | Current native `read` interface or scoped `linkbrain_read`; visible Odoo read schemas only when the exact model is authorized | Read only; do not invent connectors |
| `write_file` | Native `write`/`edit` to the requested private draft artifact | No HRIS/ATS/policy mutation or message |
| `list_dir` | Use an already-known approved path | No callable directory listing is assumed |
| `get_tool_details` | Inspect the currently supplied native tool schema plus owner toolcard | Not a callable tool alias |
| `linkskills_use` | Retrieve already-qualified releases | Do not treat draft/uncertified packs as qualified |

Current visible Odoo read names, if supplied and scoped: `odoo__search_records`, `odoo__count_records`, `odoo__read_records`. Actual schemas and access scope govern. No shell or source-skill connector names are assumed.
