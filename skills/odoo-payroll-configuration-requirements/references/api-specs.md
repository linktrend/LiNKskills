# Native interface map

| Canonical metadata label | Supported consumer mapping | Limit |
|---|---|---|
| `read_file` | Native `read` or scoped `linkbrain_read`; Odoo read APIs only with supplied schemas | Read-only, exact current schema governs |
| `write_file` | Native `write`/`edit` for requested private draft | Never mutate finance/Odoo/business records |
| `list_dir` | Known approved path only | No callable alias assumed |
| `get_tool_details` | Inspect supplied schema and owner toolcard | Not a callable tool |
| `linkskills_use` | Qualified release retrieval | This draft is unqualified |

Potential Odoo reads are `odoo__search_records`, `odoo__count_records`, `odoo__read_records` only when actually exposed and authorized. The original source scripts and command examples are preserved but never run by this pack.
