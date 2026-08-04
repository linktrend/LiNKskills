# Deviation Process and Execution-to-Verification Handoff

- **Status:** Accepted (Phase 0)
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §2, §29.5, Phase 0 items 13–14, Phase 11 classifications

## 1. Approved-plan control

Execution agents implement the approved plan. They do not silently reinterpret architecture, ownership, permission-to-act, or interface gates.

Frozen interfaces change only through a new version and a handoff to every affected consumer.

## 2. Deviation process

If a contradiction appears or a deviation seems necessary:

1. **Stop** dependent work that would bake in the deviation.
2. **Record** the proposed change, reason, and evidence of the contradiction.
3. **Identify** every affected plan, repository, interface, and file.
4. **Notify** the LiNKskills Codex verifier and the LiNKbrain coordinating agent.
5. **Wait** for a plan-level decision before continuing the dependent path.
6. Continue only safe unrelated work (fake-backed, local, docs, tests) that does not assume the deviation.

Do not guess, weaken certification, bypass ownership, or take over another owner’s surfaces.

## 3. Deviation record (minimum fields)

```text
deviation_id:
date:
requester_agent: LiNKskills Cursor/Grok
approved_plan_hash: 31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88
summary:
reason_and_evidence:
proposed_change:
affected_plans:
affected_repositories:
affected_interfaces_or_gates:
affected_files:
blocked_work:
safe_work_continuing:
decision_needed_from:
status: proposed | accepted | rejected | superseded
```

## 4. Execution-to-verification handoff

Every Grok execution handoff (and the final LiNKskills implementation handoff) must include:

- approved phases/issues claimed complete;
- changed files and intentionally untouched ownership boundaries;
- branch, worktree, commits, session, plan hash, release/profile hashes, and cross-repository contract hashes;
- commands, tests, evals, and validation results;
- migrations, configuration, credentials, deployments, and live actions performed, including who performed them;
- Cursor canary duration/scenarios/counts/failures/rollback when applicable;
- fake, integration, stage, production, certification, release, telemetry, and Librarian evidence tiers actually obtained;
- failures, deviations, blockers, residual risks, and omitted work;
- reproduction and rollback instructions;
- evidence locations suitable for independent Codex verification;
- a plan-item-to-evidence index for the LiNKskills Codex verifier.

## 5. Verification classifications

The Codex verifier maps each planned item to exactly one of:

1. implemented and proven;
2. implemented but not proven live;
3. partially implemented;
4. omitted;
5. implemented differently from plan;
6. blocked by another repository/interface;
7. outside the execution agent’s ownership.

A Grok completion report is **provisional** until repository Codex verification (and shared-interface LiNKbrain Codex reconciliation where applicable) completes. The verifier reports deficiencies and returns correction packets to the original Grok owner; it does not silently take over implementation without Principal approval.

## 6. Relation to interface gates

Bypassing an accepted gate in `docs/inventories/cross-plan-interface-gates.md` is a deviation. Fake-backed progress behind a gate is allowed; declaring the gated outcome complete is not.
