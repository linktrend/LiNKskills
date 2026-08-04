# LiNKskills Librarian Domain Worker Contract v0.1

- **Status:** Accepted contract sketch for Phase 0 handoff
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §18, §29.4 Librarian gate
- **Related ADR:** 0008 (ownership), 0006 (executed evidence)

## 1. Purpose

Define the versioned interface between:

- **Producer:** LiNKskills domain-worker logic, policies, and tests;
- **Host:** LiNKplatform generic Librarian runner (`packages/librarian-runner` and related shared files).

Integration into the generic host is a coordinated LiNKplatform work packet. Domain agents must not independently edit shared runner files.

## 2. Ownership

| Asset | Owner |
|---|---|
| This contract, Skills worker package, domain tests, fixtures | LiNKskills |
| Worker loading, scheduling, retries, credentials, audit/alerts, shared runner files | LiNKplatform |
| Brain domain worker | LiNKbrain (separate contract) |

## 3. Worker identity

- Institutional agent: Librarian (one identity).
- Domain workflow key: `linkskills` (name finalizable; must not collide with Brain).
- Runtime principal example: `svc_lskills_librarian` (Platform-issued; never actor-distributed).

## 4. Invocations (logical)

Host invokes versioned Skills worker operations. Exact package entrypoints may evolve; semantics are fixed:

| Operation | Input (conceptual) | Output (conceptual) |
|---|---|---|
| `intake_normalize` | Candidate skill ref, provenance | Normalized Skill Pack v0.1 mapping, gaps, overlap notes |
| `diagnose_performance` | Telemetry/feedback window, skill/profile refs | Prioritized improvement candidates (redacted) |
| `propose_trace_to_eval` | Failed/corrected run refs | Redacted eval candidate proposal |
| `run_eval_profile` | Execution-profile identity + suite/tool hashes | **Hashed Eval Runner result with executed case evidence** (ADR 0006) |
| `recommend_certification` | Eval Runner evidence receipt | Promote / hold `eval_pending` / demote / escalate — never without evidence |
| `propose_source_change` | Diagnosis + branch intent | Branch/PR metadata + evidence links |
| `propose_lifecycle` | Deprecate/retire/rollback intent | Lifecycle recommendation + migration guidance |
| `propose_consolidation` | Overlap set | Merge/split/routing proposal; high-impact cases escalate to Principal |

## 5. Evidence rules

- Certification recommendations require signed/hashed Eval Runner results containing actual case outputs/artifacts/tool results/deterministic checks.
- Prompt-only scoring from skill ID + rubric names is **non-certifying**.
- Telemetry/feedback inputs must already be redacted per ADR 0007; worker must not ingest raw Brain conversations or private memory.
- Worker must not hide regressions or unresolved evidence gaps.

## 6. Autonomy and forbidden actions

Allowed through normal integration: normalize, diagnose, branch, modify Skills domain source, run evals, open PRs, recommend clean internal releases.

Forbidden:

- bypass CI/evals or repository integration;
- push directly to `staging` or `main`;
- rewrite published immutable versions;
- grant Program permissions;
- auto-apply low-confidence/high-impact merge/split without Principal review;
- edit LiNKplatform shared runner files from the Skills agent;
- apply live shared migrations.

## 7. Host integration handoff (LiNKplatform packet)

LiNKskills delivers:

- versioned worker package / artifact hash;
- this contract version;
- fake fixtures and conformance suite;
- required scopes/credentials (names only);
- schedule/retry expectations;
- failure and escalation taxonomy.

LiNKplatform delivers:

- host loading wiring without merging Brain/Skills data planes;
- operational monitoring;
- proof the shared runner invokes the versioned contract only.

LiNKskills then runs domain conformance validation against the integrated host.

## 8. Compatibility

- Contract changes are additive version bumps (`v0.1` → `v0.2`); frozen interfaces change only via new version + consumer handoff.
- Separate Brain worker contract remains mandatory; no combined worker API.
