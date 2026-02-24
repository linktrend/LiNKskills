# Example Trace: Refiner Mode

## Scenario
User asks to improve `email-responder` after repeated HITL pauses and adds a new feature for attachment validation.

## Trace
**User**: "Run skill-architect in REFINER MODE for email-responder and add attachment validation."

**Action**: Select mode `REFINER`.
**Action**: Read root `execution_ledger.jsonl` and `email-responder/references/old-patterns.md`.
**Action**: Build diff plan:
- tighten input schema to require attachment metadata
- add fail-fast Decision Tree check for unsupported attachment types
- add feature logic for attachment validation
- increment version and update `references/changelog.md`

**Action**: Apply updates and run `validator.py` + `global_evaluator.py`.

**Response**: Skill refined to v1.1.0 with schema hardening, earlier error detection, and feature-level updates.

