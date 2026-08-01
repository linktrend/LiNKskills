# LiNKskills Production Execution Prompt

Use **Cursor Grok 4.5 High** for this entire task. Every subagent you spawn must also use **Cursor Grok 4.5 High**. Spawn as many useful Grok 4.5 High subagents as the environment permits and parallelize independent work aggressively, while keeping one primary agent responsible for integration, ownership, validation, and the final handoff.

The prompt file `docs/CURSOR-GROK-PRODUCTION-EXECUTION-PROMPT-2026-07-30.md` may initially appear as the sole untracked Principal-supplied control document. Preserve it, treat it as authorized input rather than conflicting work, and include it in the first cohesive documentation/implementation commit.

Continue the existing LiNKskills implementation end to end from branch `issue/21-linkskillsdevelopmentplan01` at exact starting HEAD `af1177a6428e3128b5360da5b92aecd670502589`. Before editing, verify the branch, HEAD, upstream, clean status apart from this prompt, worktrees, active sessions, and latest handoffs. If the exact tip has advanced, inspect the added commits and proceed only when compatible and unowned; record the new authoritative start SHA. Do not discard, rewrite, or overwrite existing work.

## Principal authority and objective

The Principal authorizes completion of LiNKskills toward production using the safest approved four-plan architecture. Complete the maximum LiNKskills-owned work possible in this one packet and continue through every gate that becomes objectively satisfied. Do not stop merely to report progress. Stop only for a hard gate requiring unavailable external owner evidence, destructive action, paid-resource approval, or another repository's implementation.

The selected security direction is Platform-owned PACI: ES256 JWT access tokens carrying frozen AuthClaims, 15-minute lifetime, no refresh token, private-key client authentication, JWKS verification, and introspection for defined high-risk writes. LiNKplatform owns issuance, keys, credentials/runtime bindings, live migrations, infrastructure, secrets, and the generic Librarian host. LiNKskills owns Skills contracts, resource-server verification/authorization, immutable releases and profiles, real evaluation, Gateway/MCP behavior, Skills persistence adapters and migration source packages, Cursor consumer readiness, and the Skills Librarian domain worker.

Never delete, replace, recreate, reset, or overwrite an existing project, database, schema, migration history, credential, secret, or production dataset. Never create a paid resource or incur new/increased ongoing cost without returning a concise cost/necessity packet to the Principal first. Never print secrets. CI and Bugbot polling are deferred; do not wait for or rerun them. Use rigorous local evidence and leave independent Codex verification open.

## Required reading and authority

Read in full before modifying code:

- `AGENTS.md`
- `README.md`
- `docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`
- `docs/LINKSKILLS-INTENT.md`
- `docs/LINKSKILLS-TECHNICAL-PRD.md`
- `docs/LINKSKILLS-OPERATIONS-MANUAL.md`
- `docs/OPEN-ISSUES.md`
- `docs/handoffs/2026-07-29-grok-certification-correction-wave12.md`
- `docs/handoffs/2026-07-30-linkskills-authclaims-package-pin-0.2.2-correction.md`
- `docs/adr/0009-confined-executor-network-isolation.md`
- `docs/runbooks/PRODUCTION_OPERATIONS.md`
- `evidence/phase7/cursor-canary-status.json`
- `evidence/phase10/skill-classification-draft.json`
- the latest LiNKplatform PACI specification, implementation handoff, frozen AuthClaims/PACI contract, and environment-readiness evidence;
- the latest OpenClaw and LiNKbrain consumer handoffs relevant to Skills sequencing.

Verify and record the plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`. Treat sibling repositories as read-only evidence and never edit them.

## Parallel work allocation

Register one unique active session and declared file ownership, then spawn Grok 4.5 High subagents for non-overlapping lanes such as:

1. PACI resource-server verifier and adversarial conformance.
2. Cursor machine-token client/canary integration.
3. Postgres persistence, migrations, RLS, idempotency, and recovery.
4. Gateway/MCP packaging, health, deployment artifacts, and operations.
5. Eval Runner isolation, immutable release/profile proof, and catalog classification.
6. Skills Librarian domain worker, stage scenarios, canary evidence, and handoffs.

The primary agent must inspect and integrate all subagent work. Subagent summaries are not proof.

## Required implementation

### 1. PACI-secured Skills Gateway

Consume the Platform-owned frozen PACI implementation contract once published:

- ES256 JWT verification with strict issuer, audience, algorithm, key ID, expiry, not-before, token type, AuthClaims version, actor, runtime binding, service, organisation, and exact permitted-operation checks;
- same-origin/no-redirect JWKS retrieval, bounded cache and refresh, key rotation, unknown-key handling, outage behavior, and fail-closed rules;
- exact `platform.auth-claims/1.1.0` behavior unless a newer Principal-approved frozen contract supersedes it;
- no unsigned path outside explicit local-test injection;
- no caller-minted identity, shared-secret fallback, database credential, `service_role`, signing key, or local production token minting;
- Platform-defined introspection for the exact high-risk Skills writes, bounded and fail closed;
- independent request/audit correlation, safe errors, privacy-preserving logs, and no raw token/claim leakage;
- adversarial tests for unsigned/invalid signatures, algorithm confusion, wrong issuer/audience/service/operation/environment/actor/org/binding, unknown key, expired/not-yet-valid/revoked/rotated credentials, cross-domain reuse, replay, outage, and introspection failure.

Prefer a versioned Platform Python verifier/helper when the Platform owner publishes one. If it is not available, implement a narrow versioned adapter against the reviewed contract/fake and mark it `implemented but not proven against frozen Platform service`; provide an exact delta packet. Do not invent a competing security contract.

### 2. Skills-owned Cursor token client and canary path

Implement the project-scoped Cursor consumer path for PACI `client_credentials` with `private_key_jwt`:

- separate Skills client identity and least-privilege operations;
- 15-minute access token, no refresh token, safe early renewal, bounded retry/backoff, replay-safe assertion `jti`, expiry handling, revocation, and fail closed behavior;
- secrets supplied only through approved secret references/files/injection, never command arguments, logs, Git, fixtures, or handoffs;
- exact downstream Skills endpoint/audience and no reuse for Brain or OpenClaw;
- safe project-scoped launcher/config template and diagnostics that reveal status but not secret material;
- static-bearer examples retired or explicitly local-test only.

Do not edit shared/global Cursor configuration or running Cursor process state without a separately coordinated maintenance window. Keep the integration project-scoped and supply an exact application handoff.

### 3. Production persistence and tenant isolation

Replace local-only storage assumptions with production adapters consistent with the approved `lskills` schema while retaining SQLite/in-memory only for explicit local/test use:

- Gateway runs, events, feedback, idempotency reservations/fences, external-side-effect intents/results, and audit data;
- immutable publication registry and exact replay/content-conflict behavior;
- Skills Librarian domain store interface and adapter, without editing Platform's generic runner;
- transaction-scoped actor/organisation context, RLS, same-tenant binding, wrong-actor/wrong-org denial, and context non-leakage;
- durable idempotency with request hashes, leases, fencing, stale reclaim, commit-before-cache publication, crash/retry recovery, and honest at-least-once external-effect semantics;
- retention, deletion, backup/restore, migration upgrade, rollback, and partial-failure handling.

Use additive deterministic migrations and update the hashed migration manifest. Prove fresh and upgrade application, RLS, concurrency, crash/retry, rollback, and recovery with ephemeral Postgres. Platform alone applies migrations live.

### 4. Deployable Gateway and MCP service

Produce deterministic installable/deployable Skills Gateway and MCP artifacts:

- exact approved `skills_*` surface and HTTP/MCP parity;
- strict request/response/error schemas, size/time limits, privacy filters, operation authorization, and immutable bundle/profile enforcement;
- readiness/liveness/metrics/audit surfaces without content or secret leakage;
- dependency readiness, graceful drain/shutdown, buffering/retry, offline recovery, and honest degraded behavior;
- production dependency/package proof with no development-only imports;
- least-privilege environment/SecretRef templates and Platform-consumable service definition using existing architecture;
- updated `docs/runbooks/PRODUCTION_OPERATIONS.md` and deploy documentation reflecting the current long-lived Gateway rather than the historical checkout-only posture.

Do not revive the retired Logic Engine or archived production stack. Do not create a combined Brain/Skills service.

### 5. Certification, isolation, releases, and catalog readiness

Complete the real execution-backed certification path:

- certifiable Linux execution uses proven path-scoped filesystem and network isolation (`bwrap` or an already approved container/VM path); macOS-unproven isolation cannot certify;
- sealed issuer-signed receipts bind suite, release, profile, executor, network isolation, permitted operations, result hashes, and evidence;
- prompt-only, suite-authored output, unverifiable receipt, incompatible profile, missing release, or contradictory evidence fails closed;
- deterministic shared hashing across publisher, validator, Eval Runner, profile stamping, Gateway, and replay;
- recursively enforce input/output/telemetry privacy and no conversation data;
- validate all canonical artifacts and run real isolated evals for every intended launch target;
- classify the full catalog honestly and promote only evidenced releases/profiles; leave insufficient entries draft, deprecated, or retired.

No paid execution host may be created without Principal cost approval. Local/free existing resources may be used when safe and isolated.

### 6. Librarian domain worker

Complete the Skills-owned worker and its Platform host contract:

- receipt-bound evidence rules, immutable release/version handling, provenance, conflict escalation, retry/dead-letter, idempotency, and privacy;
- no prompt-only certification and no Brain-domain behavior;
- exact configuration, migrations, health, smoke, rollback, and versioned handoff for Platform's generic host;
- local fake-host and ephemeral-database proof.

LiNKplatform alone integrates and operates the generic live host.

### 7. Stage readiness and canaries

Prepare the complete Skills stage packet: artifact hashes, migration manifest, PACI verifier/client pins, endpoint/audience/credential requirements, service definition, runbooks, alerts, failure/recovery cases, rollback, evidence schema, and minimum scenario/run/activity counts.

When Platform supplies independently verified stage endpoint, migrations, PACI issuer/JWKS/introspection, separate Skills credentials, secret injection, service hosting, backup/restore, audit, and rollback receipts, continue in this same packet through Skills-owned stage validation and Cursor canary stages:

1. authenticated read-only discovery;
2. exact bundle/profile retrieval;
3. non-side-effecting execution and telemetry;
4. exact governed tool execution;
5. credential rotation/revocation and service-outage behavior;
6. offline buffer/recovery and idempotency;
7. supervised Librarian dry-run;
8. at least three active operating days plus approved minimum run/scenario counts, whichever is longer.

Do not begin a production canary or claim general launch until independent Cursor readiness and Codex interoperability verification exist and the OpenClaw/Lisa Skills prerequisite gate is satisfied. Skills may follow Brain; it must not block Brain's earlier launch.

Supply immutable Codex and OpenClaw fragments/contracts/conformance to their owners, but never edit their live/shared configuration.

## Verification and handoff

Run the full relevant local proof without waiting for hosted CI/Bugbot:

```bash
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
python3 -m unittest discover -s tests/skill_runtime -v
PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:." python3 -m pytest -q
git diff --check origin/development...HEAD
```

Also run new PACI, Postgres/RLS, packaging, isolation, privacy, rollback, and failure/recovery proofs. Record all failures and reruns. Scan changed files/evidence for secrets.

Commit cohesive changes with conventional commits and push the existing issue branch. Do not merge, rebase, force-push, mark the PR ready, promote branches, or self-certify. Promotion follows independent Codex verification and satisfied cross-repository/live gates.

Produce a complete provisional handoff under `docs/handoffs/` containing exact start/code/clean pushed heads, all changed files, contracts/hashes, tests and failures, local/fake/stage/production evidence separation, migrations/deployment/canary packets, live actions and operators, rollback, outstanding owner gates, and a seven-classification ledger for the entire approved Skills plan.

Close the implementation session cleanly and stop for LiNKskills Codex independent verification only after all currently possible LiNKskills-owned work is complete.
