# Native interface and execution limits

- Contract labels `read_file`, `write_file`, `list_dir`, and `get_tool_details` are not callable tools.
- `read_file` maps only to native `read` on known authorized paths. `write_file` maps only to native `write`/`edit` for a user-authorized draft artifact.
- `list_dir` is not available; use a known path. `get_tool_details` means inspect the current native tool schema and owner toolcard before a connector action.
- No shell/CLI, e-discovery, case-management, docket, email, calendar, legal research, Drive, or source-system connector is assumed. Do not use Claude-specific paths from the upstream source.
- If the requested read/write or current-law verification route is absent, work from supplied evidence and report the capability gap.
- OpenClaw runtime state is consumer-owned SQLite. The heavy-profile JSONL state field is an authoring contract only; checkpoint through the supported consumer owner interface and keep privileged content out of state/telemetry.
- All outputs are draft-only; effectful actions are excluded and must not be represented as completed.
