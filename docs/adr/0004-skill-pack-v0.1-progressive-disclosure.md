# ADR 0004 — Skill Pack v0.1 and Progressive Disclosure (Levels 0–6)

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §10)
- **Context source:** Plan §10 (Skill Pack v0.1), current `format_profile: simple|heavy` catalog, ADR 0002

## Context

The current catalog uses minimal frontmatter plus `simple` / `heavy` layout profiles. The long-form commercial Skill Pack format is too heavy for every skill at internal launch, while the minimal frontmatter is too weak for routing, typed dependencies, certification, and progressive disclosure.

Launch needs a v0.1 standard between those extremes that preserves the useful simple/heavy distinction.

## Decision

**1. Adopt Skill Pack v0.1 as the launch source standard.** Every published skill version declares:

- **Identity / release:** stable `skill_id`, display name, semantic version, description, capability category, provenance/author/source, license for imported material, source commit and content hash at publication, release channel and lifecycle state, format/schema version, compatible runtime profiles and minimum capability tier.
- **Routing:** when to use / not use, task/capability tags, exclusion and ambiguity rules, related/alternative/superseded/prerequisite skills, recommended disclosure starting level.
- **Execution contract:** required/optional inputs (structured schema where applicable), output/artifact contract, procedure and conditional branches, forbidden actions and failure handling, verification steps, completion criteria, known limitations.
- **Typed dependencies (not one untyped list):** `skill_dependencies`, `packaged_tools`, `host_capabilities`, `external_services`, `library_assets`, `runtime_requirements`, `optional_dependencies` / certified alternatives.
- **Eval / telemetry declarations:** eval-suite path/schema/hash, required certification profiles, verification refs, telemetry classification and redaction rules, artifact/evidence retention, performance/cost budgets where relevant.

**2. Progressive-disclosure fragment levels 0–6 are mandatory addressable surfaces:**

| Level | Fragment |
|---|---|
| 0 | Existence / index entry |
| 1 | Routing / metadata |
| 2 | Short summary and requirements |
| 3 | Applicable procedure section |
| 4 | Verification / failure section |
| 5 | Examples or schemas |
| 6 | Full internal Skill Pack when explicitly required |

Default selection remains summary-first. Internal actors may request deeper fragments; full packs are not the default disclosure.

**3. Preserve `format_profile: simple` and `heavy`.** Do not force every skill into the largest layout. Legacy parsing may assist source migration only; published runtime consumes v0.1 compiled fragments and descriptors.

## Consequences

- Authoring meta-skills (`skill-template`, `skill-architect`, `tool-architect`) migrate to v0.1 before bulk catalog migration.
- Catalog entries gain category, hashes, toolchain/profile compatibility, and release semantics beyond draft filesystem snapshots.
- Disclosure APIs (`skills_fragment_get` and equivalents) serve addressable levels, not only whole-file loads.
- Migration reports must cover all current skills without collapsing simple skills into heavy layouts.
