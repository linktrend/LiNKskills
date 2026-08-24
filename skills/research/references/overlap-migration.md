# Overlap and migration decision

| Existing primitive | Decision | Canonical outcome |
| --- | --- | --- |
| `search-strategy` | Migrate useful tier routing and HITL rules | New research workflows use `research` v1.0.0; the prior skill remains immutable and independently addressable for legacy callers. |
| `citation-enforcer` | Compose, do not duplicate | `citation-enforcer` remains an independently composable claim-evidence gate and is a dependency of `research`. |
| `tools/research` | Exclude | The consumer or owning runtime retains transport and connector implementation; this packet creates no tool folder. |

Migration is explicit and supersedes new broad-workflow use: callers selecting `search-strategy` for a new broad
research workflow should select `research` instead. Existing exact releases are
not rewritten, and rollback removes only the new draft qualification/mapping.
