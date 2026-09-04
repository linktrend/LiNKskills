# Source-only interface and provenance

The only interfaces are the JSON contracts at `schemas.json#/definitions/input` and `schemas.json#/definitions/output` plus the deterministic CLI wrapper in `../scripts/helper_tool.py`. There is no native service, direct API, MCP execution path, connector, Program authority, live Platform binding, publication operation, or LiNKtarget write operation.

`source-provenance.json` binds the local authoritative methodology inputs by version and SHA-256 digest to the package rules, schemas, and eval cases. Consumer data is never a methodology source.
