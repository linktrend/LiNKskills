# Handoff — LiNKskills Internal Launch Detailed Development Plan

## 1. Session outcome

Created and then cross-plan-aligned the standalone proposed development plan for finishing and internally launching LiNKskills:

- `docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`

The alignment used the complete revised LiNKbrain Phase 1 plan as a compatibility input. The LiNKskills plan now accepts the same shared-surface ownership, concurrent-execution, interface-gate, and independent-verification model.

No product code, database migration, service, credential, runtime configuration, shared Codex/Cursor setting, deployment, or live integration was changed.

## 2. Scope completed

- Reconciled the Principal-approved LiNKskills decisions, original long-form manual, current repository, and current next-step gaps.
- Re-read the revised 1,753-line LiNKbrain plan in full, including its product boundaries, architecture, identity, Librarian, actor integration, ownership, execution, risk, done, and approval sections.
- Preserved LiNKbrain and LiNKskills as separate products and services with independently named `brain_*` and `skills_*` MCP tools.
- Assigned canonical actor identity/authentication/credential issuance to LiNKplatform and limited LiNKskills to domain bindings referencing platform actor IDs.
- Assigned `lskills` migration authoring/testing to LiNKskills and sole shared stage/production review/application/operation to LiNKplatform.
- Split institutional Librarian ownership between LiNKskills domain-worker logic and the LiNKplatform generic host/integration/operations.
- Assigned all OpenClaw/Lisa implementation and live-profile surfaces to the OpenClaw Prime agent.
- Assigned shared Codex host configuration to the LiNKbrain execution agent by default for this four-agent rollout; LiNKskills supplies a separate fragment and validates its own behavior.
- Preserved LiNKskills ownership of the Cursor-first product canary while protecting shared/global Cursor development settings.
- Added cross-plan interface gates, approved-plan deviation control, execution handoff requirements, and independent plan-conformance verification.

## 3. Files changed

- `docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`
- `docs/handoffs/2026-07-27-codex-linkskills-internal-launch-plan.md`

No other file or repository was changed.

## 4. Repository and branch

- Repository: `/Users/linktrend/Projects/LiNKskills`
- Branch: `dev/minicodex/planninglinkskills`
- The two planning documents are the only intended work products of this planning task.
- Do not treat this handoff as authority to apply migrations, credentials, runtime configuration, or live rollout.

## 5. Product and shared-foundation decisions

- Git owns editable Skill Pack/tool/eval source; LiNKplatform-backed registry/storage owns published operational state and immutable bundles.
- LiNKskills has a protocol-independent core with separate MCP/API adapters and `skills_*` tools.
- LiNKbrain has its own service/schema/worker and `brain_*` tools; there is no combined Brain/Skills Gateway or shared mutable domain data.
- Brain and Skills retain independent credentials/scopes, caches, queues, telemetry, retention, failures, feature flags, and rollback.
- They share only LiNKplatform-defined actor/organisation claims, correlation IDs, credential/deployment/audit/observability conventions, and generic Librarian worker-host lifecycle.
- Cross-service correlation uses opaque references. LiNKskills never consumes raw Brain conversations/private memory as telemetry; LiNKbrain does not duplicate Skill Packs, eval artifacts, or certification evidence.
- Permission-to-act remains outside LiNKskills permanently.

## 6. Repository ownership decisions

- **LiNKskills:** Skill Packs, tools, evals, certification, registry behavior, Gateway, MCP/API, domain migration source/policies, Cursor canary, domain worker, fragments/fakes/conformance, and validation.
- **LiNKplatform:** canonical actor identity/authentication/credential issuance, shared infrastructure conventions, sole live migration application, and generic Librarian host/loading/scheduling/retries/credentials/audit/observability/operations.
- **LiNKbrain:** separate Brain domain/worker and, for this rollout, default ownership of shared Codex `config.toml`, common hook registration, and common Codex-side lifecycle scripts.
- **OpenClaw Prime:** managed MCP, plugins/modules, hooks, buffers/outboxes, Lisa actor/session mapping, live profile, integration tests, rollout, and rollback.

Domain agents do not edit another repository or a shared file unless a coordinated work packet transfers exact ownership. In particular, LiNKskills and LiNKbrain agents must not independently edit the same existing `LiNKplatform/packages/librarian-runner` files.

## 7. Interface gates

1. **Identity:** LiNKplatform publishes the canonical actor/auth claim contract.
2. **Migration:** LiNKskills supplies a tested, hashed migration manifest; LiNKplatform alone applies it live.
3. **Librarian:** LiNKskills publishes a versioned domain-worker contract; LiNKplatform integrates it into the generic host.
4. **OpenClaw:** Brain and Skills supply separate contracts/fakes/conformance; OpenClaw owns implementation.
5. **Codex:** both domains supply separate fragments; the shared integration owner applies only ready services.
6. **Production:** domain agents do not independently enable production credentials, apply migrations, or modify Lisa's authoritative profile.
7. **Cursor maintenance:** prefer project-scoped canary configuration; any unavoidable global mutation requires a coordinated maintenance window and rollback proof.
8. **Verification:** no Grok completion or shared interface is accepted without repository Codex verification and applicable LiNKbrain Codex reconciliation.

## 8. Execution and verification model

Four repository-specific Cursor agents using Grok 4.5 High Fast execute the four approved plans concurrently. Each must have an assigned repository, separate checkout/worktree, dedicated branch, session/ownership record, and implementation handoff.

Four Codex 5.6 Sol Medium agents independently verify the matching implementations. The LiNKskills Codex agent verifies LiNKskills; the LiNKbrain, LiNKplatform, and OpenClaw Codex agents verify their repositories. The LiNKbrain Codex agent then reconciles the four verified results.

A Grok completion report is provisional. The verifier checks actual files, tests, evals, migrations, configuration, live evidence, and plan coverage. It reports deficiencies and creates a correction work packet for the original Grok owner; it does not silently take over implementation without Principal approval.

Every planned item is classified as:

- implemented and proven;
- implemented but not proven live;
- partially implemented;
- omitted;
- implemented differently from plan;
- blocked by another repository/interface;
- outside the execution agent's ownership.

## 9. Approved-plan control

Execution agents implement the approved plans. If a deviation appears necessary, the agent must stop dependent work, record the proposed deviation and reason, identify affected plans/repositories/interfaces/files, send it to the repository Codex verifier and LiNKbrain coordinating agent, and wait for a plan-level decision.

Using Cursor as the development environment grants no authority over shared/global Cursor rules, MCP, hooks, extensions, IDE Development symlink targets, or user settings. LiNKskills owns only the approved Cursor product canary. Any unavoidable global mutation follows the maintenance gate in Section 21.2 of the plan.

## 10. Execution-to-verification handoff requirements

The LiNKskills Grok handoff must include:

- approved phases/issues claimed complete;
- changed files and intentionally untouched ownership boundaries;
- commands, tests, evals, and validation results;
- migrations, configuration, credentials, deployments, and live actions performed, including the actual owner/operator;
- failures, deviations, blockers, residual risks, and omitted work;
- reproduction and rollback instructions;
- evidence locations suitable for independent Codex verification;
- cross-repository contracts produced/consumed, including versions and hashes.

## 11. Rollout compatibility

- LiNKskills rollout: Cursor first, Codex second, Lisa/OpenClaw third.
- LiNKbrain rollout: Lisa first, Codex second.

These do not conflict because each service has independent readiness gates and feature flags. OpenClaw may enable Brain before Skills. Shared Codex configuration includes only services that passed their own readiness gate.

## 12. Current-state proof retained from planning

- registry validation: 53 targets passed;
- catalog freshness: 34 skills current;
- runtime unit tests: 6/6 passed;
- service ownership: 35 services passed;
- catalog state: 34 draft, 32 heavy, 2 simple;
- top-level packaged tools: 19;
- two non-blocking legacy `execution_ledger.jsonl` warnings remain.

These results describe the planning-time baseline. They are not proof that the proposed launch architecture has been implemented.

## 13. Main implementation risks

- current certification is prompt-only and does not execute complete eval suites;
- current authoritative docs still describe the narrower Git-checkout runtime;
- shared/global Cursor changes could disrupt four concurrent Grok sessions;
- concurrent Brain/Skills edits to shared Codex or Librarian files could collide;
- a domain agent could incorrectly apply a shared live migration;
- raw Brain data could leak into Skills telemetry without strict schemas/conformance;
- an execution agent could claim completion without live or independent proof.

The aligned plan contains explicit mitigations and ownership gates for each risk.

## 14. Planning-document validation

- detailed plan headings are sequential from Section 1 through Section 34;
- implementation phases are sequential from Phase 0 through Phase 11;
- all ten Markdown code fences are balanced;
- both changed files end with a newline and contain no trailing whitespace or tab characters;
- all six named cross-plan gates and all seven plan-conformance classifications are present;
- Git status confirms only the two LiNKskills planning documents are new in this repository;
- LiNKbrain, LiNKplatform, and OpenClaw Prime were inspected read-only and not changed by this task.

## 15. Exact next action

The Principal reviews and approves or annotates the aligned plan. After approval, create four repository-specific execution work packets and begin only independently owned Phase 0/contract work. Do not cross an identity, migration, Librarian, OpenClaw, Codex, Cursor-maintenance, production, or verification gate until its named owner supplies the required evidence.
