# Skill Changelog

## Unreleased — source proposal (2026-10-05)
- Refiner reports now bind the exact target path and SHA-256 before patch generation and stop when observed bytes differ.
- Structural validation, semantic findings, and behavior receipts have separate typed report fields; missing consumer evidence remains `NOT_EVALUATED` and schema validity is not qualification.
- SCAFFOLD, REVERSE_ENGINEER, existing REFINE editing steps, and the existing `.workdir/tasks/{{task_id}}/state.jsonl` persistence contract are preserved.
- This proposal does not resolve consumer-native session aliases or change validators, adapters, runtime state, or release gates.

## v1.5.0 - 2026-07-15
- Added right-sized template awareness: SCAFFOLD now selects a `format_profile` (`heavy` default, `simple` for stateless single-pass skills), per catalog-eval-telemetry-spec §5.
- Documented `format_profile` in `references/manifest-spec.md` and pointed simple scaffolds at `../skill-template/references/simple-profile.md`.
- Relaxed the "no minimalist skills" scope-out into "no simple-profile skills that actually need resumable state" (simple profiles are now legitimate).

## v1.4.0 - 2026-02-22
- Migrated skill location to `/skills/skill-architect`.
- Updated scaffolding references to target `/skills/[skill-name]`.
- Added explicit fallback to `/skills/tool-architect` when required global tools are missing.
- Updated validator/evaluator invocation paths for new directory layout.

## v1.3.0 - 2026-02-20
- Enforced Global Tooling & Persistence Protocol (CLI-first levels and exception policy).
- Added mandatory `tooling` frontmatter block for generated/migrated/refined skills.
- Switched architect persistence checkpoint path to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Added Specialist/Generalist profiling and conditional JIT requirements (`get_tool_details`, schema caching).

## v1.2.0 - 2026-02-20
- Added required `engine` frontmatter contract for intelligence-floor enforcement.
- Added explicit Decision Tree intelligence-floor fail-fast gate.
- Aligned architecture workflow to generate/maintain engine requirements in target skills.

## v1.1.0 - 2026-02-20
- Added explicit multi-mode architecture: `SCAFFOLD`, `REVERSE_ENGINEER`, `REFINER`.
- Added reverse-engineering Structural Audit protocol (Steps A-D).
- Added Phase 0 Improvement & Migration Audit.
- Added versioning discipline (`release_tag`) and changelog mandate for generated/refined skills.

## v1.0.0 - 2026-02-20
- Initial skill scaffolding architecture.


## Unreleased Jane reviewed correction — 2026-10-05

- Integrated exact independently accepted source correction; preserved legacy modes and draft identity. Model qualification and publication remain unclaimed.
