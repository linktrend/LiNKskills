# Wave 0 — Foundation Packets

## Rules for every packet

- Start from the manifest's refreshed approved baseline in an isolated `issue/*` worktree.
- Acquire and read back the packet-repository lease and durable heartbeat before mutation.
- Change only owned paths; generated catalogue files belong to PKT-24.
- Use test-first changes and synthetic fixtures. Record exact commit/tree, scoped diff, commands/results, and independent Terra verification.
- Checkpoint and push only. The Phase Packager integrates accepted commits; implementers do not open or merge PRs.
- Code/test failure returns to development on a new identity; infrastructure gets at most two attempts on one candidate; ordinary repairs stop after three.
- Stop on an unresolved interface, licence, ownership collision, unavailable required Autowork discovery, or missing founder approval for a reserved action.

## PKT-00 — Baseline reconciliation and architecture approvals

**Objective:** Convert the approved requirements into accepted architecture decisions without changing product behavior.

**Inputs:** PRD, frozen interfaces, remote `main` v2.5.1 identity, existing ADRs 0001–0009, current source/classification inventory.

**Work:**

1. Re-read the exact remote baseline and compare provider, schema, catalogue, Librarian, Google vendor tree, and consumer handoffs with the PRD classifications.
2. Record ADRs for provider-v2 standard MCP/local execution and external vendor/adaptation/update lineage; amend an existing ADR instead when it already owns the decision.
3. Record the proposed schema/protocol/migration blast radius and cross-repository handoffs.
4. Obtain founder approval bound to the approved manifest digest before PKT-01 starts.

**Acceptance:** No competing PRD or taxonomy; every durable decision has one authority; exact baseline and tree are recorded; reserved changes are explicitly approved or held.

**Evidence:** Baseline inventory, ADR decision table, manifest digest, approval record, clean documentation diff.

**Rollback:** Revert documentation commit; no runtime state exists.

## PKT-01 — Provider taxonomy and release metadata contracts

**Objective:** Define versioned schemas before provider or importer implementation.

**Work:**

1. Add schemas and positive/negative fixtures for taxonomy nodes, collection manifests, per-resource provenance/licence, vendor/adapted lineage, update candidates, eligibility metadata, role-pack manifests, and exact-resource descriptors.
2. Preserve compatibility with existing release/digest/attestation primitives; extend rather than duplicate them.
3. Specify lifecycle/selectability states and deterministic mappings from vendor labels to provider taxonomy.
4. Prove unknown trust-boundary fields and incomplete provenance fail closed.

**Acceptance:** Schemas are versioned, bounded, deterministic, and reject unsafe/ambiguous records; role packs contain references only; no schema grants authority.

**Evidence:** Contract test results, fixture inventory, compatibility report, schema digest.

**Rollback:** Revert additive contracts before any dependent migration/release is published.

## PKT-02 — Standard MCP v2 discovery and exact resource retrieval

**Objective:** Turn the v2 gate into a standard MCP provider that returns real governed resources.

**Work:**

1. Add failing tests for initialize/capability negotiation, family/category pagination, exact qualified release reads, byte/digest equality, and denied lifecycle/profile cases.
2. Implement bounded resource enumeration and reads over the protocol-independent core.
3. Apply Platform identity plus Skills selectability; expose awareness metadata separately from selection/content.
4. Remove intended-architecture exposure of provider-side run/tool execution and add explicit legacy-adapter metrics/removal criteria.
5. Extend the client fixtures for OpenClaw standard MCP conformance without editing OpenClaw.

**Acceptance:** Exact resources contain actual immutable bytes; identity/role/task/qualification/compatibility denials fail closed; large collections do not flood results; legacy execution operations are unavailable on v2.

**Evidence:** MCP transcript fixtures, exact digest receipts, positive and denial tests, legacy transition matrix.

**Rollback:** Restore the prior provider entrypoint and disable the new version; no immutable release is altered.

## PKT-03 — External collection vendor/adaptation/update lifecycle

**Objective:** Implement the reusable lifecycle once for every external source.

**Work:**

1. Implement immutable vendor release ingestion, per-file inventory/provenance/licence, collection manifests, linked adaptations, and update candidates.
2. Add Librarian outcomes `accept`, `adapt`, `postpone`, and `reject`, with diff/licence/security/compatibility/eval/customization/feedback evidence.
3. Add rollback/current-pointer behavior that never auto-switches on candidate arrival.
4. Package additive `lskills` migrations and hashed migration manifest; do not apply shared live migrations.
5. Define the signed idempotent candidate contract for LiNKautowork.

**Acceptance:** Vendor bytes remain unchanged; unsafe originals are preserved but nonselectable; adaptations link explicitly; duplicate candidate delivery is idempotent; no importer activates a collection.

**Evidence:** Fresh/upgrade migration tests, deterministic inventory tests, candidate idempotency tests, Librarian transition tests, rollback proof.

**Rollback:** Forward-fix or revert unpublished migrations; restore prior current pointer; preserve immutable records.

## PKT-04 — External-content security, privacy, evaluation, and Librarian controls

**Depends on:** PKT-03.

**Objective:** Make untrusted imported/private-domain content fail closed before qualification.

**Work:**

1. Add synthetic adversarial fixtures for prompt injection, hidden authority escalation, undeclared network/file effects, destructive instructions, licence gaps, digest drift, and private-data leakage.
2. Extend evaluation evidence to bind source/release identity, declared effects, compatibility, and privacy findings.
3. Enforce minimal telemetry and reject raw prompt, transcript, secret, health, calendar, email, Drive, battery, selfie, image, identifier, and private feedback content.
4. Prove the Librarian cannot mutate active production releases outside review/promotion controls.
5. Add a negative assertion forbidding the rejected automatic emergency-support wording/behavior.

**Acceptance:** Every malicious/incomplete candidate is rejected or quarantined; no private fixture contains real data; telemetry retains only approved bounded fields; qualification requires clean executed evidence.

**Evidence:** Adversarial results, privacy-negative report, telemetry field audit, qualification refusal receipts.

**Rollback:** Revert unpublished evaluator/validator changes; never weaken existing privacy controls to restore compatibility.
