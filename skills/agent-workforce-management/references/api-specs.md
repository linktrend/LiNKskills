# API and ownership specifications

## Input

The local helper accepts a JSON workforce request matching
`references/schemas.json#/definitions/input`. Evidence is explicit and
namespaced. Role, rule, capability, delegation, monitoring, quality, and
proposal records are descriptive.

## Output

The result is a deterministic owner-review envelope. `READY_FOR_OWNER` means
the supplied evidence and shape are sufficient for review; it does not mean
approved, activated, suspended, retired, granted, or scheduled. `DRAFT` marks
uncertainty. `BLOCKED` marks an authority, privacy, duplicate, or contract
violation.

## Ownership matrix

| Concern | This skill | Owning system or person |
| --- | --- | --- |
| Reusable role draft | prepares proposal | named owner / consumer |
| Brain-rule applicability | records supplied evidence | Brain rule owner |
| Capability or skill request | prepares bounded request | Platform and technical grant owner |
| Domain delegation | prepares owner-scoped proposal | Program owner / consumer |
| Workload and quality observations | summarizes supplied evidence | workforce consumer |
| Suspend or retire proposal | prepares safe review artifact | named owner and operations authority |
| Credentials and private memory | never handles or copies | credential and private stores |
| Activation, scheduling, transport, mutation | never performs | consumer runtime and owning systems |

## Non-overlap

This family complements `department-head`, `executive-decisions-governance`,
`time-management`, and `executive-sync-8am`. It does not replace their state,
decision, calendar, task, reporting, or transport ownership and does not write
`configs/` or `catalog/index.json`.
