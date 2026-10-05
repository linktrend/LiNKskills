# Native interface

Tool labels are contract vocabulary only. Map `read_file` to native `read` on a known authorized path; `write_file` to native `write`/`edit` for the specifically requested draft; `get_tool_details` to inspection of current native schema and owner toolcard. `list_dir` is not callable. Checkpoints use the consumer owner interface; OpenClaw runtime state remains SQLite-owned. Do not run source scripts, shell commands, or external services.
