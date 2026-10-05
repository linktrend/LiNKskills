# Known failure patterns

- Turning an unverified citation into a binding regulatory requirement.
- Dropping an explicit scope limitation from a policy diff.
- Deduplicating distinct obligations solely because they share a policy.
- Writing a tracker, closing/accepting a gap, or sending a notice from a proposal task.
- Assuming recipient, owner or cadence configuration that was not supplied.

## 2026-10-05 contract refinement

A `completed_draft` status is not evidence of task completion. Require populated task-specific deliverable sections and evidence refs; when material facts are missing, preserve `missing_inputs` and `unknown_facts` under `needs_context` and do not force blank sections into a completed result. Portable heavy-template JSONL metadata is not runtime persistence: OpenClaw checkpoints use the supported consumer-owned SQLite interface.
