# Cross-Repository Handoff Packets

These packets are roadmap dependencies, not entries in the LiNKskills repository-bound execution manifest. Before execution, each owning repository must create its own schema-valid manifest, exact baseline, issue/worktree, lease, heartbeat, tests, evidence, and rollback. LiNKskills supplies frozen contracts and conformance fixtures only.

## XPKT-01 — LiNKplatform identity and migration operations

**Owner:** LiNKplatform.

**Inputs:** PKT-01 claims/eligibility contracts; PKT-03 migration manifest; PKT-04 privacy controls.

**Work:** Review/freeze identity claims and technical eligibility; review/sequence/apply `lskills` migrations in approved environments; host generic Librarian integration without merging Brain/Skills state; issue application/readback/rollback receipts.

**Prohibited:** Skill bodies, taxonomy authority, consumer activation, combining Brain/Skills workers or schemas.

**Acceptance:** Least-privilege identity/migration proof, exact manifest hash, stage then separately approved production receipts, rollback/forward-fix.

## XPKT-02 — OpenClaw standard MCP v2 consumer

**Owner:** OpenClaw Prime.

**Inputs:** PKT-02 conformance fixtures; PKT-22 Lisa manifest; validated instance-template schemas; `LISA-CANARY-BINDINGS.md`.

**Work:** Replace legacy discovery/provider-run architecture with standard MCP negotiation and exact release retrieval; verify digests locally; enforce profile pins and tool permissions; preserve separate private SQLite T-ID/health/battery/selfie state; implement and test every value in `LISA-CANARY-BINDINGS.md` as validated instance overrides; implement rollback. Do not activate future agents.

**Prohibited:** Copying reusable skill bodies/templates into profiles, treating Skill selectability as permission, exposing private state/credentials, combining Brain/Skills failure state.

**Acceptance:** Authorized Lisa sees permitted families, retrieves only pinned qualified releases, executes locally, denies inactive/unqualified/tampered content, preserves native runtime, and rolls back exact pins.

## XPKT-03 — LiNKautowork upstream polling

**Owner:** LiNKautowork, subject to founder confirmation of the recommended boundary.

**Inputs:** PKT-03 signed idempotent candidate contract.

**Work:** Deterministically poll configured upstreams on a bounded schedule, calculate inventory/content/licence/diff facts, and submit one idempotent candidate. Do not qualify, publish, change current pointers, or activate.

**Acceptance:** Duplicate polls do not duplicate candidates; failed/partial scans fail closed; credentials/logs are redacted; Skills readback binds the accepted candidate.

## XPKT-04 — Lisa canary, hosted rollout, and rollback

**Owner:** OpenClaw Prime for consumer/profile; LiNKskills for provider; Platform for claims/migrations; deployment owner for host/VPS.

**Depends on:** PKT-25, XPKT-01, XPKT-02; XPKT-03 required when callable.

**Work:** Prove exact authenticated provider discovery/retrieval, local execution, minimal telemetry, instance overrides, four Lisa skill families, authorized Workspace subset, privacy denial, degraded behavior, and rollback. Stage/VPS/production actions require their own approvals.

**Acceptance:** Exact source/consumer/environment identities align; Lisa alone is canary; no future-agent activation; schedules/account bindings/private data remain consumer-owned; proof classes remain distinct.

## XPKT-05 — Independent cross-repository verification

**Owner:** Independent verifier/coordinator assigned under IDE Development.

**Work:** Inspect—not merely copy—provider, Platform, Autowork, OpenClaw, hosted, VPS, and production receipts; verify ownership and privacy boundaries; reconcile every cross-repository gate and report correction packets to original owners.

**Acceptance:** No unsupported PASS, no silent takeover, and no closure until exact receipts match the PRD definition of done.
