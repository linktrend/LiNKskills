# LiNKskills 1.0 — Agent and Operator Guide

**Release:** LiNKskills 1.0.0
**Repository:** `https://github.com/linktrend/LiNKskills`
**Production source ref:** `main`
**Current protected identity:** commit `e40bf0dac697eca74a49d956189d2a87f728fbd6`, tree `d5b3410ccf4a383fba71ace86e8904a6dceb1270`
**Deployment target:** LiNKserver 01 (the production Server 01 host)

This is the compact source of truth for an AI agent joining the LiNKskills repository. It explains what the software is, what it owns, how it is built, how it is operated, and where the production source is pinned. Historical plans, prompts, handoffs, issue packets, and superseded readiness reports are under [`docs/archive/`](archive/).

## 1. What the software does

LiNKskills is LiNKtrend’s central catalog of reusable AI procedures. A skill is a versioned directory containing instructions, supporting references or scripts, and a baseline evaluation suite. The catalog index makes skills discoverable. The publisher turns accepted source into immutable release bundles. The Gateway and MCP adapter expose the `skills_*` operations for search, description, progressive loading, invocation metadata, usage receipts, and feedback. The Librarian domain worker turns observed usage and evaluation evidence into proposed improvements.

LiNKskills provides procedures and evidence. It does not decide whether an agent may send a message, spend money, deploy software, or act for a customer. Governance, entitlements, capability grants, and program ledgers belong to LiNKplatform and to each consuming Program. LiNKbrain is a separate knowledge service.

## 2. Runtime shape

- `skills/`: the catalog of skill packages.
- `catalog/index.json`: generated machine-readable discovery index.
- `packages/contracts`: schemas and frozen interoperability contracts.
- `packages/core`: catalog, lifecycle, disclosure, certification, and hashing rules.
- `packages/publisher`: immutable bundle construction.
- `packages/eval_runner`: executable evaluation runner; prompt-only certification is rejected.
- `packages/tool_runtime`: tool descriptors and invocation runtime.
- `packages/gateway`: stdlib HTTP Gateway and persistence adapters.
- `packages/mcp_server`: MCP adapter over the Gateway service.
- `packages/client`: client, compatibility loader, and offline telemetry buffer.
- `packages/librarian_domain`: Skills-owned Librarian domain worker and install contract.
- `lib/skill_runtime`: compatibility checkout loader retained during migration.
- `supabase/migrations`: packaged database migrations; live application is owned by LiNKplatform/Server 01.
- `evidence/`: retained certification and delivery evidence referenced by tests and receipts.

## 3. How an agent uses it

1. Identify the Program and actor identity. LiNKskills never invents authority.
2. Discover a published skill through the Gateway/MCP `skills_*` surface, or use a pinned checkout only where a consumer is still in migration.
3. Load only the progressive fragments needed for the task.
4. Perform the action under the consuming Program’s own approval and safety rules.
5. Record usage and feedback through the Gateway; local buffering is used when the shared store is unavailable.
6. Treat a release as usable only when the applicable evaluation, publication, provider binding, and consumer evidence exists.

Never copy secrets into the repository. Never enable `local-test` authentication on staging or production. Never start the retired Logic Engine.

## 4. Build and validation

The repository is Python-first and requires Python 3.11 or newer. The Gateway is a standard-library HTTP service; PostgreSQL support is optional through the package extra. MCP is an adapter over the same service and contracts. CI runs catalog validation, package tests, ownership checks, security scanning, and protected release gates.

Useful local commands:

```bash
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
python3 -m unittest discover -s tests/skill_runtime -v
PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:." python3 -m pytest -q
python3 scripts/check-service-ownership.py
```

For production-like operation, install the domain packages in dependency order and follow [`docs/runbooks/PRODUCTION_OPERATIONS.md`](runbooks/PRODUCTION_OPERATIONS.md). The local sealed evaluator is a development tool; it is not a production deployment mechanism.

## 5. Production operation on Server 01

Server 01 owns the live checkout, container/image, secrets, database connection, restart, health checks, rollback, and external consumer activation. LiNKplatform owns shared migration application and Platform PACI authority. LiNKskills owns source, contracts, catalog, Gateway/MCP code, evaluation logic, telemetry domain behavior, and the non-secret handoff packets.

The production source pin for LiNKskills 1.0 is the exact `main` identity above. A deployment must record the source commit and tree, image digest, migration set, health/readiness result, restart result, and rollback identity. Use the Server 01 handoff and rollback documents in [`docs/integrations/server01/`](integrations/server01/) and the production runbook. Do not infer runtime state from a Git ref alone; read the deployment receipt or host readback when operating the server.

Required production settings include production authentication, the Platform authenticator, PostgreSQL-backed storage, a state path, and the trusted token-minting/introspection configuration. Missing production credentials or an unreachable store must fail closed.

## 6. Release and branch rules

Only these three long-lived branches are valid:

- `development`: integration branch.
- `staging`: release candidate.
- `main`: production candidate and LiNKskills 1.0 source pin.

Changes flow through an issue branch and protected pull request into `development`, then through protected promotion pull requests to `staging` and `main`. Temporary issue, phase, promote, and review branches are disposable delivery machinery and must be deleted after the release is complete. Do not push directly to `staging` or `main`, bypass checks, or self-approve a protected merge.

The top-level product version is 1.0.0. Protocol and package contract versions such as the frozen PACI envelope remain at their independently versioned values; changing those is a compatibility decision, not a consequence of the product release label.

## 7. Ownership and escalation

- **LiNKskills:** catalog, packages, contracts, Gateway/MCP, eval runner, telemetry domain, Librarian domain, docs, and release source.
- **LiNKplatform:** shared Postgres migration apply, capability registry, PACI issuer/JWKS/introspection, generic Librarian host, and shared identity/grant authority.
- **Server 01 operations:** production checkout/image, environment secrets, service lifecycle, backups, health/readiness, rollback, and runtime readback.
- **Consumers (OpenClaw Prime, Codex, Cursor, LiNKautowork):** host configuration and actor-specific bindings, using identities issued by Platform.

When a task crosses those boundaries, create a non-secret handoff with the exact repository, commit, tree, release ID, and requested owner action. Do not put credentials in a handoff or commit.

## 8. Troubleshooting rules

- A failing catalog or eval gate means the release is not publishable.
- A missing Platform identity or grant is a Platform/consumer blocker, not something LiNKskills can create.
- A failed `/ready` probe usually means authentication configuration or the shared store is unavailable; inspect the service logs and deployment receipt.
- If a source commit or tree changes, all receipts bound to the previous identity are invalid until regenerated.
- For rollback, pin the prior recorded production commit/image and use the Server 01 rollback procedure.

For historical reasoning, read the archived packet that introduced the decision. For current behavior, trust the code, current protected refs, current deployment receipt, runbooks, and this guide.
