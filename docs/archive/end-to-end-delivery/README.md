# LiNKskills end-to-end delivery

**Status:** `PLANNING_INTERFACE_READY / ED-00_READY_AFTER_APPROVE / GROK_QUEUE_HOLD`
— the package is a review candidate; implementation, provider mutation,
consumer activation, live migration, deployment, and production acceptance
await a literal `APPROVE` in the owning task. The first Grok worker, ENV-00,
also awaits current-task queue ownership.

**Planning issue:** [linktrend/LiNKskills#323](https://github.com/linktrend/LiNKskills/issues/323)

This directory is the stable entry point for making the existing LiNKskills
service on LiNKserver 01 operational. It is an operational delivery overlay, not
a replacement for the approved product architecture or the later catalogue
expansion plan.

## Founder outcome

Delivery is done only when a founder or authorised actor can use Cursor, Codex,
and Lisa/OpenClaw to discover one of the five initial qualified Skills releases,
retrieve and verify its exact immutable content, execute it locally under the
consumer's own authority, and submit bounded use/feedback evidence; the
Librarian and operator can observe that evidence; failure, revocation, restart,
backup, and rollback paths are demonstrated on the assigned production server.

A merged branch, green test, healthy container, successful `/health`, source
catalogue entry, local SQLite publication, or consumer configuration by itself
does not meet that definition.

## Initial delivery versus later expansion

The required initial provider-delivered set is frozen to the five
LiNKskills-owned releases already identified as qualified in the installed IDE
lock:

- `git-safeguard@1.1.0`
- `persistent-qa@1.0.0`
- `repository-manager@1.0.0`
- `skill-template@1.2.0`
- `tool-architect@1.0.0`

`agentsetup@1.3.0` and `agentcomply@1.3.0` remain required local bootstrap
adapters and are not claimed as provider catalogue skills. Their continued local
availability prevents a bootstrap deadlock.

The other 54 entries in the current 59-entry source catalogue, the six
initial-seed collection adapters, and all 207 external collection members are
**later catalogue expansion**. Existing source, immutable bundles,
classification, quarantine, and disabled activation manifests are preserved,
but this delivery does not bulk-qualify, globally enable, or activate them.

Functional usability and strict internal-launch completion are reported
separately. `FUNCTIONAL_ACCEPTED` requires the three ordered representative
actor flows. The binding internal-launch plan also requires multi-day Cursor
use, so `INTERNAL_LAUNCH_COMPLETE` remains HOLD until a 48-hour observation
spanning at least two Asia/Taipei dates passes; continuous paid activity is not
required.

## Package index

| Document | Authority and use |
|---|---|
| [End-to-end PRD](./PRD.md) | Complete observable product and operational acceptance for this delivery. |
| [Starting position](./STARTING-POSITION.md) | Evidence-classified source, installed configuration, and demonstrated-live baseline. |
| [Work packets](./WORK-PACKETS.md) | Atomic implementation, configuration, integration, deployment, recovery, and acceptance packets. |
| [Execution manifest](./EXECUTION-MANIFEST.json) | IDE Development 2.5.2 / Coding Execution Protocol 1.0.1 packet graph. |
| [Execution route](./EXECUTION-ROUTE.md) | Operative REST dispatcher, authenticated read-only proof, exact packet contract, and first executable packet. |
| [OSS inventory](./OSS-INVENTORY.md) | Existing versus required software, sole owners, configuration, and connections. |
| [Readiness report](./READINESS-REPORT.md) | Planning completeness, factual reliability, route practicality, and remaining gates. |

## Product and architecture authority

The following existing files remain authoritative; this package links rather
than copies them:

1. [`docs/LINKSKILLS-INTENT.md`](../LINKSKILLS-INTENT.md) — product purpose,
   boundaries, and Program-level definition of done.
2. [`docs/LINKSKILLS-TECHNICAL-PRD.md`](../LINKSKILLS-TECHNICAL-PRD.md) — core
   architecture, storage, evaluation, telemetry, and operational model.
3. [`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](../LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md)
   — approved launch decisions, ownership, actor order, and acceptance.
4. [`docs/provider-v2-operations.md`](../provider-v2-operations.md) and
   [`docs/provider-v2-consumer-conformance.md`](../provider-v2-consumer-conformance.md)
   — current resource-first provider contract. Provider v2 excludes
   `skills_run_*` and `skills_tool_*`; consumers execute locally.
5. [`docs/runbooks/PRODUCTION_OPERATIONS.md`](../runbooks/PRODUCTION_OPERATIONS.md)
   and [`docs/deploy/GATEWAY-MCP-SERVICE-DEFINITION.md`](../deploy/GATEWAY-MCP-SERVICE-DEFINITION.md)
   — service, health, configuration, drain, and rollback contract.
6. [`docs/INITIAL-SKILL-SEED-ROUTING.md`](../INITIAL-SKILL-SEED-ROUTING.md) —
   later collection admission boundaries.
7. [`docs/planning/governed-skill-expansion/README.md`](../planning/governed-skill-expansion/README.md)
   — later expansion only; it does not authorize this deployment or bulk
   activation.

## Reviewed immutable baselines

| Surface | Revision reviewed | Meaning |
|---|---|---|
| LiNKskills protected `development` | commit `7a813f529f7b25a40fd3e88f74fb0e86c7c728d5`, tree `d0bb392351994810173f730c47b63112c31e391b` | Planning and future implementation baseline. |
| LiNKskills protected `main` and deployed release | commit `7067716fef5189a1427a7cf9b0847cec898e19de`, same tree `d0bb392351994810173f730c47b63112c31e391b` | Exact source currently staged and imaged on LiNKserver 01. |
| Platform protected `development` | commit `dde2640f35a1cfa10f9e907b2acd1791e729d40c`, tree `6d221b8c0807f9eb43164770ebb65fc944607fd3` | Current upstream repository baseline observed during active recovery. |
| Platform shared-foundation plan | blob `7477a17d4189f0dad950ca326ea42c89b0e8c072`, SHA-256 `b942f0a9a94875379b0f63222df719fc6a04ee6f05b0bac78775e6d5e8dc61e0` | Approved ownership and interface authority reviewed. |
| Platform recovery task | task `01a0843c-0df9-74e2-907a-05c5f736d6ed`; status snapshot `2026-09-10` | Active upstream recovery, not a claim of Platform operational completion. |

Any implementation run must refresh these identities before dispatch. A changed
commit or tree invalidates prior candidate reviews and receipts.

## Authority boundary

Planning documents may be committed and pushed under issue `#323`. Before
`APPROVE`, no product files, packages, dependencies, database state, secrets,
accounts, provider state, consumer configuration, server services, protected
branches, or production routes may be changed. Platform remains solely owned by
the separate LiNKserver 01 Deployment Recovery task.

Deployment Advisor acceptance releases this package for downstream planning
only. It never supplies founder `APPROVE`, queue ownership, implementation
authority, live mutation authority, or production acceptance.

Once recorded, the single literal `APPROVE` covers all documented execution,
publication, consumer activation, Server 01 deployment, observation, promotion,
and production-acceptance actions. No second packet-stage approval is required.
Only materially changed scope, access, spend, or destructive action beyond the
documented recovery procedures requires fresh founder direction.
