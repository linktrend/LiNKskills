# Native interface map

- `read_file` → current native `read` on known approved paths.
- `write_file` → native `write`/`edit` only for an explicitly requested internal draft.
- `get_tool_details` → inspect visible native schemas and owner toolcards; no callable alias.
- `linkskills_use` / `linkbrain_read` → only if the current schema exposes the exact read operation.
- No assumed shell, external legal search API, calendar, email, or source-system write interface.
