# Data and integration boundary

This analytical skill does not assume external APIs, providers, brokers, or paid-data entitlements. `native_session_read` and `native_artifact_write` are logical capability labels that must map to tools actually exposed by the host; do not call a tool by an invented name. Validate inline schemas using the host's available structured-output facility; if none exists, inspect field presence manually. Do not claim a `get_tool_details` capability unless the host actually exposes it. Use only data supplied by the user or a currently connected, approved read-only source. Record source, terms/access status, timestamp, units, and vintage. Do not call execution APIs; adapters and any runtime integration belong to Eric and the existing LiNKtrading engine.


The included `scripts/helper_tool.py` is an auditor/developer CLI helper only, not a tool exposed to Jane. Jane uses only the host native session and artifact read/write capabilities actually provided. Do not create JSON task state, trace, ledger, or telemetry sidecars.
