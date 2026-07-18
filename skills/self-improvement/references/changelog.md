# Changelog

## v1.1.0 - 2026-07-15 — Promote to the Librarian
- Retriggered as async/periodic curation (scheduler or telemetry-volume threshold) instead of reactive in-session use; updated `usage_trigger` and added an explicit Invocation Model + Decision Tree gate.
- Wired eval-suite re-runs into evidence gathering: Phase 3 now runs each candidate's `references/eval-suite.yaml` and factors rubric scores + `delta_vs_previous` alongside ledger telemetry; a missing eval suite is recorded as a gap, never silently skipped.
- Made the promotion decision explicit (Phase 4): auto-promote toward `usable` only on a clean, no-regression eval improvement (equal-or-better on every rubric dimension, no size/complexity blowup); any regression, ambiguity, blowup, or missing suite escalates to `eval_pending`/`PENDING_APPROVAL`; a failing eval on a `usable` version auto-demotes it.
- Consumes richer telemetry (`program_ref`, `duration_ms`, `cost`, `outcome_detail`) to prioritize targets.
- Engine tier unchanged: `min_reasoning_tier: high` / `preferred_model: gpt-5` (frontier-tier judgment, per spec §6/§7).

## v1.0.0 - 2026-02-24
- Added ledger-driven self-improvement workflow.
- Added requirement to include user-requested feature upgrades in plan inputs.
