# Changelog

## Draft candidate LR-WP-003 - 2026-08-31
- Added supports/contradicts/qualifies/cites methods and negative-evidence
  classification. Cyclic and self-referential claim links block finalization.
- No certified release is claimed.

## v1.1.0 - 2026-07-15
- Adopted `format_profile: simple` (right-sized template, catalog-eval-telemetry-spec §5).
- Removed the persistence block and task-state machinery this stateless single-pass gate never used; replaced the full Decision Tree/multi-phase workflow with a short Preconditions list and a single enforcement pass.
- Kept the CLI-first tooling protocol, Memory/Search/File evidence typing, input/output contracts, and the mandatory Phase 5 ledger/telemetry append.

## v1.0.0 - 2026-02-24
- Added evidence-first citation enforcement workflow.
- Added Memory/Search/File source typing requirements.
