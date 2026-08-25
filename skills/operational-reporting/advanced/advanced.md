# Operational reporting decision rules

Use the narrowest mode that answers the supplied request. Normalize every
record to `(kind, status, owner, window, evidence_pointer)` before synthesis.

- Morning and evening windows are input labels, not permissions to query a
  schedule. Compare deltas only inside the supplied window.
- `verified_completed` is the only status eligible for a completed-work section.
  `reported`, `proposed`, `blocked`, and `unknown` remain labeled.
- Remove empty sections after filtering. If nothing material remains, use the
  one-line no-change mode.
- A deadline is a date/time by which work is due; never turn an event start time
  into a deadline.
- A missing or stale evidence pointer blocks `READY_FOR_OWNER` and is reported
  as uncertainty.
- A final checkpoint records the verification pointer and owner; it never asks
  for another reading or claims transport delivery.
