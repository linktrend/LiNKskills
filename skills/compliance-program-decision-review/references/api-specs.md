# Native tool, interface, and persistence boundary

The Golden Template frontmatter retains its canonical tool names as contract metadata; those labels do not prove native interfaces exist for Sara. Map `read_file` to a currently visible native read. Map `write_file` to a currently visible native write/edit, and only for an authorized internal draft at a known approved path. `list_dir` and `get_tool_details` are unavailable assumptions here; do not invent them or claim their invocation. If an applicable native tool exposes its own detail lookup, use that exact native interface.

The copied upstream Python scripts and their assets/references are preserved source material only. Do not run or present them as task tools. They read/write files by their own contracts and have not been reviewed or adapted as Sara integrations. The offline `scripts/helper_tool.py` is only an input-schema checker; it makes no business or compliance decisions.

The canonical frontmatter `persistence.state_path` is retained as Golden Template metadata, not an instruction to create a JSONL file. Use only the supported consumer-owned SQLite checkpoint interface when currently available and authorized. Do not create local JSONL or other runtime sidecars. If that SQLite interface is unavailable, keep the review draft-only and disclose the missing checkpoint route.
