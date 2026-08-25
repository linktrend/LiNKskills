# Time-management interface

`planning_request` is supplied by the consumer and contains synthetic or
redacted evidence, task intake, external mappings, capacity periods, and an
optional review/report mode. A `time_management_result` returns stable task
references, confirmation and status decisions, priority order, capacity-aware
period proposals, evidence requirements, review/report sections, and an
explicit effects envelope. The helper never opens SQLite or writes Tasks,
Calendar, Brain, a Program Ledger, email, Telegram, or a handoff.

The private coordination store remains the OpenClaw consumer's authority for
minting permanent `T-` IDs. LiNKskills may preserve an already supplied ID or
return a deterministic fixture ID for evaluation only; it must not claim to
persist that ID.
