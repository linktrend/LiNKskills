# Cross-Plan Interface Gates

- **Status:** Accepted this session (Phase 0)
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §29.4 (gates), §29.5 (deviation), §21.2 (Cursor maintenance)

## Rule

Agents may work concurrently on independently owned Phase 0 and contract tasks. They may not bypass these gates because another plan is unfinished. Crossing a gate requires the named owner’s evidence; LiNKskills may continue fake-backed / local work while waiting.

## Accepted gates

### 1. Identity gate

- **Requirement:** LiNKplatform publishes the canonical actor/auth claim contract and fixtures.
- **LiNKskills may:** develop against fakes and publish claim requirements/conformance tests.
- **LiNKskills may not:** declare live authentication complete before the platform contract and fixtures exist.
- **Evidence owner:** LiNKplatform (contract); LiNKskills (acceptance tests against fakes, then live).

### 2. Migration gate

- **Requirement:** LiNKskills supplies a versioned migration manifest, tests, evidence, and rollback/forward-fix instructions.
- **LiNKplatform alone:** reviews, sequences, and applies shared live migrations.
- **LiNKskills may not:** apply stage/production migrations independently or claim live schema readiness from unapplied SQL alone.
- **Evidence owner:** LiNKskills (package); LiNKplatform (live apply).

### 3. Librarian gate

- **Requirement:** LiNKskills and LiNKbrain publish separate versioned worker contracts.
- **LiNKplatform:** integrates them into the generic host and owns shared runner files.
- **Domain agents:** run their own conformance validation; must not independently edit shared `librarian-runner` files.
- **Evidence owner:** Domain (contract + conformance); LiNKplatform (host integration).

### 4. OpenClaw gate

- **Requirement:** Brain and Skills provide stable separate contracts, fakes, configuration fragments, and conformance suites.
- **OpenClaw Prime:** owns implementation and may enable Brain before Skills.
- **LiNKskills may not:** edit OpenClaw internals or Lisa’s profile without an explicit ownership-transfer work packet.
- **Evidence owner:** OpenClaw Prime (implementation); LiNKskills (Skills conformance validation).

### 5. Codex gate

- **Requirement:** Both domains provide independently named configuration fragments.
- **Shared integration owner (default LiNKbrain for this rollout):** applies only services that passed their own readiness gate.
- **Each domain:** validates its own configured behavior.
- **LiNKskills may not:** concurrently edit shared Codex host configuration.
- **Evidence owner:** Shared config owner (apply); LiNKskills (Skills validation).

### 6. Production gate

- **Requirement:** Domain agents do not independently enable production credentials, apply live migrations, or modify Lisa’s authoritative profile.
- **Evidence owner:** Named live operator per action (normally LiNKplatform / OpenClaw / Principal as applicable).

### 7. Cursor maintenance gate

- **Requirement:** Prefer isolated/project-scoped configuration.
- **Any unavoidable global mutation** requires the stop → impact → maintenance-window → validation → rollback procedure in plan §21.2, including confirmation that the other three Grok sessions will not be disrupted.
- **Evidence owner:** LiNKskills execution agent for product canary; coordinated window for global changes.

### 8. Verification gate

- **Requirement:** No implementation or interface is complete solely because its Grok owner reported success.
- **Required:** Repository Codex verification and, for shared interfaces, LiNKbrain Codex reconciliation.
- **Evidence owner:** Matching Codex verifier(s); Grok handoff is provisional.

## Session acceptance

These eight gates are accepted as binding for LiNKskills Phase 0+ execution on 2026-07-27. Deviation from an accepted gate follows `docs/contracts/deviation-and-verification-handoff.md`.
