# Supported consumer interface mapping

| Canonical metadata label | Supported interpretation | Limits |
|---|---|---|
| `read_file` | Current native `read` interface or scoped `linkbrain_read`; visible Odoo read schemas only when the exact model is authorized | Read only; no invented connectors. |
| `write_file` | Native `write`/`edit` to the requested private draft artifact | No HRIS/ATS/policy mutation or external message. |
| `list_dir` | Use an already-known approved path | No callable directory listing is assumed. |
| `get_tool_details` | Inspect the currently supplied native tool schema plus owner toolcard | Not a callable alias. |
| `linkskills_use` | Retrieve already-qualified releases | Draft/uncertified packs are not treated as qualified. |

This workflow needs no custom CLI, shell execution, source script or external write.
