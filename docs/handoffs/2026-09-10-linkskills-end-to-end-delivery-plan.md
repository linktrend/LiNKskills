# LiNKskills end-to-end delivery planning handoff

**Date:** 2026-09-10

**Status:** `PLANNING_INTERFACE_READY / ED-00_READY_AFTER_APPROVE / GROK_QUEUE_HOLD / AWAITING ADVISOR ACCEPTANCE AND APPROVE`

**Planning issue:** `#323`

**Branch:** `issue/323-plan-linkskills-end-to-end-deployment-on-linkser`

## Delivered

- Stable entry point: `docs/end-to-end-delivery/README.md`
- Operational PRD: `docs/end-to-end-delivery/PRD.md`
- Evidence baseline: `docs/end-to-end-delivery/STARTING-POSITION.md`
- Atomic packets and dependency order: `docs/end-to-end-delivery/WORK-PACKETS.md`
- Protocol manifest: `docs/end-to-end-delivery/EXECUTION-MANIFEST.json`
- Governed route/start gate: `docs/end-to-end-delivery/EXECUTION-ROUTE.md`
- OSS inventory: `docs/end-to-end-delivery/OSS-INVENTORY.md`
- Readiness decision: `docs/end-to-end-delivery/READINESS-REPORT.md`

The initial provider-delivered set is five existing LiNKskills releases:
`git-safeguard`, `persistent-qa`, `repository-manager`, `skill-template`, and
`tool-architect`. `agentsetup` and `agentcomply` remain local bootstrap adapters.
All other source catalogue entries and external collection members are later
expansion and remain unqualified/inactive unless separately approved.

## Current operational truth

Protected LiNKskills `development` is `7a813f529f7b25a40fd3e88f74fb0e86c7c728d5`
with tree `d0bb392351994810173f730c47b63112c31e391b`. The Server 01
container is built from protected `main` `7067716fef5189a1427a7cf9b0847cec898e19de`
at the same tree and image digest
`sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f`.
It is live and healthy, but not ready: `/ready` returns 503 because the Postgres
store probe reports `OperationalError`. The service loads 59 draft Skills and
rejects unauthenticated requests, but valid identity, v2 provider, qualification,
selectability, consumer use, Librarian, backup/restore, and production acceptance
are not proven.

Platform remains solely owned by Deployment Recovery task
`01a0843c-0df9-74e2-907a-05c5f736d6ed`. Reviewed Platform protected
`development` was `dde2640f35a1cfa10f9e907b2acd1791e729d40c` / tree
`6d221b8c0807f9eb43164770ebb65fc944607fd3`; the shared-foundation plan blob was
`7477a17d4189f0dad950ca326ea42c89b0e8c072`. Its current recovery receipt is a
specific runtime dependency, not a planning blocker.

## Validation and authority

The manifest passed the installed Coding Execution Protocol 1.0.1 /
`V25_BOOTSTRAP_LEAN` schema and semantic validator. Package links resolve,
concurrent owned-path collisions are absent, IMP-00 is evidence-only, and any
later L-FIX ownership is conditional and dependency-ordered after ED-03/09.
JSON parsing and `git diff --check` pass.
The pushed planning commit/tree and independent
narrow-review result are appended to the task evidence after checkpointing.

No product code, dependency, credential, database, provider, consumer, server,
deployment, protected branch, or production state was changed. Implementation
begins only after a literal `APPROVE` in this task.

The operative standard-library REST dispatcher is digest-pinned. Its existing
Keychain-backed account passed safe authenticated account/model/repository reads:
Grok 4.6 Medium with Fast off is available and `linktrend/LiNKskills` is visible.
No job was launched. ED-00 is the first executable no-provider-cost packet after
`APPROVE`; ENV-00 is the first Grok worker and follows ED-00 plus a fresh XP-00
preflight. ED-01 follows ENV-00. The current queue suspension does not admit
this task as owner, so ENV-00 is not executable until the documented narrow
resume-scope update. Existing transport evidence is reused; fixture-only guard
stops are not a startup blocker. XP-00 refreshes actual route/account/repository/
identity and owner admission only; XP-05's accepted receipt already supplies
focused extension-test evidence.
XP-01 through XP-04 remain later Platform and consumer dependencies.

The single recorded `APPROVE` covers every action documented by this package,
including publication, consumer activation, Server 01 deployment, the 48-hour
Cursor observation, governed promotion, and production acceptance. There is no
second founder gate. Only materially changed scope, access, spend, or destructive
action outside the documented recovery procedures requires fresh direction.

The improvement loop reuses the repository's real Mac Mini PACI canary
issuer-policy correction at `6a2101d132b42010162595a2bab2c72fee6282da`
and its three executable regression cases. Conditional new-defect packets remain
unexecuted in `PLAN` when no new defect exists; no fictitious archive API receipt
is required. Functional
acceptance may be reported after the three representative actor flows. The
approved internal-launch plan's multi-day requirement remains explicit: strict
`INTERNAL_LAUNCH_COMPLETE` waits for a 48-hour Cursor observation spanning at
least two Asia/Taipei dates, without requiring continuous paid activity.

The Deployment Advisor's shared XP-05 lane-aware dispatcher extension is now
independently accepted: dispatcher SHA-256 `9c5b5486842e695e47f32896728ec15568237f304ea86115cde50997e419c260`,
verification SHA-256 `0a8dfbcd5f8d31157b454204e7a9fa57458c0c53f0f59558cf5f9f51718289ba`,
23 focused offline tests PASS, no provider job or live mutation. After `APPROVE`,
XP-00 owner admission, and dependency readiness, the graph-derived safe maximum
is three disjoint LiNKskills writers. The current task is integration owner;
shared manifests, migrations, interfaces, and server mutations remain serialized.

Deployment Advisor acceptance releases downstream planning only. It is not
founder `APPROVE` and authorises no implementation, provider call, queue change,
deployment, consumer activation, or production mutation.
