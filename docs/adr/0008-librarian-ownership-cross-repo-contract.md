# ADR 0008 — Librarian Ownership and Cross-Repository Contract

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §18, §29)
- **Context source:** Plan §18 (Librarian architecture), ADR 0001 Addendum (runner currently in LiNKplatform), plan §29.4 Librarian gate

## Context

The institutional Librarian is one identity with separate domain workflows. Today the runnable body lives in `LiNKplatform/packages/librarian-runner` and the LiNKskills half of the workflow is described by `skills/self-improvement/`. Concurrent Brain and Skills agents must not both edit the shared runner. Domain logic also must not be trapped forever inside a generic host package.

## Decision

**1. One institutional identity; separate domain workers.** LiNKplatform hosts one Librarian identity with separate workflows for LiNKbrain, LiNKskills, and (when separately designed) LiNKlibraries. Workflows keep separate credentials/scopes, evidence requirements, schedules, domain queues, domain contracts, telemetry, and failure states. The generic host does not merge domain workers or their data.

**2. LiNKskills owns the Skills domain worker contract, logic, and tests:**

- Librarian skill-domain requirements and schemas;
- candidate types and decision rules;
- eval and improvement execution behavior;
- source-change / publishing interfaces;
- intake, improvement, eval, consolidation, release, and retirement behavior;
- the versioned LiNKskills domain-worker implementation and conformance suite.

**3. LiNKplatform owns the generic host and existing shared runner files:**

- institutional identity;
- generic job host / scheduler / retry model;
- versioned worker loading and invocation;
- credentials and least privilege;
- shared logging, audit, and operational alerts;
- integrating versioned domain workers into `packages/librarian-runner` and related shared files.

**4. Domain agents must not independently edit shared runner files.** Neither the LiNKskills nor LiNKbrain execution agent may independently edit the same existing files under `LiNKplatform/packages/librarian-runner`. Cross-repository contracts are defined first. Integration into the generic host requires a coordinated work packet owned and executed by the LiNKplatform agent, followed by domain conformance validation.

**5. Autonomy boundary.** The Librarian may normalize, diagnose, create branches, modify domain source, run evals, open PRs, and recommend/publish clean internal releases through normal integration. It may not bypass CI/evals or repository integration; push directly to `staging`/`main`; rewrite published versions; grant Program permissions; auto-apply low-confidence high-impact merge/split decisions; or hide regressions / unresolved evidence gaps.

**6. Replace prompt-only scoring in the Skills workflow.** Host integration must consume executed Eval Runner evidence (ADR 0006). The Skills domain worker must not certify from identifiers and rubric names alone.

## Consequences

- LiNKskills publishes `docs/contracts/librarian-domain-worker-v0.1.md` (and later package implementations) as the contract producer; LiNKplatform consumes and integrates.
- Concurrent Phase 0+ work can proceed on domain contracts without colliding on shared runner files.
- ADR 0001 Addendum remains historically accurate: the current executable host is in LiNKplatform; this ADR assigns future domain-worker ownership and the edit boundary for shared files.
- LiNKbrain owns its separate domain worker under the same host pattern; LiNKlibraries expansion does not block Skills internal launch.
