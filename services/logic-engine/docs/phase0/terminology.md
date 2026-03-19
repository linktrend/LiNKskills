# Canonical Terminology Map

| Authoring Layer (Repo) | Serving Layer (Logic Engine) |
| :--- | :--- |
| Skill | Capability (`source_type=skill`) |
| Tool | Capability (`source_type=tool`) |
| Department bundle | Package |
| `task_id` | `run_id` |
| `execution_ledger.jsonl` | `run_events` + `audit_logs` |
| Skill schema refs | Capability contract refs |
| Decision Tree | Runtime policy gates |

## Naming Rules
- Public runtime identifiers come from `manifest.json` UID.
- Version defaults to manifest version unless an explicit skill frontmatter version mismatch policy is introduced later.
- Package versions are sidecar-managed and never written into `SKILL.md`.
