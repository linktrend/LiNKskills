# Overlap and migration decision

| Existing primitive | Decision | Canonical outcome |
| --- | --- | --- |
| `search-strategy` | One-way facade / supersession | New research workflows use `research` v1.0.0. This skill remains an immutable, independently addressable alias. It depends on `research`. `research` does **not** depend on `search-strategy`. |
| `citation-enforcer` | Compose, do not duplicate | Independently composable claim-evidence gate and the only skill dependency of `research`. |
| `tools/research` | Exclude | Legacy router and connector stay consumer-owned. Skills in this packet must not select `/tools/research` or `tools/research/bin/research`. |

Dependency DAG (acyclic):

`search-strategy` → `research` → `citation-enforcer`

Migration is explicit and supersedes new broad-workflow use: callers selecting `search-strategy` for a new broad
research workflow should select `research` instead. Existing exact releases are
not rewritten, and rollback removes only the new draft qualification/mapping.
No named retrieval provider is required.
