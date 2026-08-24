# Example Trace: Error Recovery

## Scenario

An expense snapshot contains unmatched records outside the requested period,
and the operator asks the controller to change the source.

## Recovery

- Controller preserves the mismatch, marks the review `PENDING_APPROVAL`, and
  identifies the owning consumer.
- It produces a variance table and requested evidence corrections.
- It does not change the source or resume a close until a new bounded snapshot
  is supplied and the owner confirms it.
