# ADR 0006 — Execution-Profile Certification Requires Executed Case Evidence

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §14–16, §18.5)
- **Context source:** Plan §16 (certification/release), §15 (Eval Runner), §7.4 (current prompt-only gap), ADR 0001 (`certification_state` is curation-internal)

## Context

The current LiNKplatform skills scoring path can receive only skill ID, version, eval-suite reference, rubric names, and a pass threshold, then ask a model to score. That proves orchestration, not skill performance. Promoting to `usable` on prompt-only judgment would falsify certification and recreate a hollow gate.

Certification must be an evidence-backed statement about a concrete execution profile.

## Decision

**1. The certification unit is an execution profile:**

```text
skill source/bundle hash
+ eval-suite hash
+ exact toolchain hashes
+ adapter version range
+ bounded runtime/model capability profile
= certified execution profile
```

Do not claim universal certification from one profile.

**2. Prompt-only scoring cannot certify.** Identifiers, rubric names, thresholds, or model assertions without executed case outputs, artifacts, tool results, deterministic checks, and retained evidence cannot promote a profile to `usable`. A model judge may score qualitative observed outputs only after the Eval Runner executes cases and supplies the observed trace.

**3. Require executed case evidence.** The Eval Runner resolves the immutable Skill Pack and exact tools, runs required cases against the target runtime profile, applies deterministic assertions before model judgment, records artifacts/evidence hashes, and aggregates an execution-profile verdict. LiNKplatform integration must consume a signed/hashed Eval Runner result containing that evidence.

**4. Lifecycle and promotion.** Compatible states remain `draft` → `eval_pending` → `usable` → `deprecated` → `retired`. Promotion requires source validation, complete required cases, no hard failure, threshold and per-dimension minimums, no prohibited regression, toolchain/profile compatibility, immutable bundle publication, and an audit/evidence receipt. Release channels distinguish development/eval, internal canary, and internal stable without becoming Program permissions.

**5. Internal-launch runtime profiles (minimum):** Cursor macOS; Codex macOS; Lisa/OpenClaw; Program-controlled executor when first needed. Profiles specify capabilities rather than pinning every harmless model patch; material changes trigger blast-radius compatibility checks.

## Consequences

- Current prompt-only `scoreSkill`-style paths are non-certifying after this ADR.
- Catalog `usable` remains a LiNKskills-internal curation gate, never Program permission-to-act (ADR 0001).
- Eval-suite YAML completeness and real runner work are prerequisites to trustworthy promotion.
- Rollbacks retarget channel pointers to prior immutable certified releases; they do not rewrite evidence history.
