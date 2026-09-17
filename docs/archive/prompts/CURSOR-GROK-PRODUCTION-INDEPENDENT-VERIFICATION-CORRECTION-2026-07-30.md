# LiNKskills Production Independent-Verification Correction Prompt

Use **Cursor Grok 4.5 High** for the primary agent and every spawned subagent. Continue branch `issue/21-linkskillsdevelopmentplan01` from exact verified HEAD `48fd7422f9fa14d39567190b54d15954b3384f8b`. Preserve this Principal-supplied prompt if initially untracked and include it in the correction commit. Spawn Grok 4.5 High subagents on explicit non-overlapping paths and complete all corrections in one wave.

This is a bounded correction after independent Codex review. Do not merge, change PR readiness, poll CI/Bugbot, apply live migrations, edit global Cursor state, contact live services, deploy, start canaries, incur cost, or self-certify. Do not edit sibling repositories.

Read the entire Skills plan, production prompt/handoff/ledger, PACI adapter/client, Gateway/MCP/persistence/Librarian/package/deploy paths, and frozen Platform authority at exact Platform HEAD `0455846487d0b8c583859060ba8b4be70e7f0b48`: `platform.auth-token-envelope/0.1.0`, `@linktrend/platform-contracts@0.3.0`, and the consumer PACI handoff. If Platform publishes a compatible correction descendant, inspect and pin it exactly.

## Corrections required

1. **Make the Cursor PACI canary path functional**
   - The project fragment currently launches the MCP server with PACI-client variables, but the MCP server never uses `PaciTokenClient`/`SkillsGatewayClient` and instead requires a static bearer.
   - Implement a project-scoped Cursor stdio MCP proxy/client that acquires short-lived PACI tokens through `SkillsGatewayClient.from_env`/`PaciTokenClient`, or integrate the same machine-token path into the MCP client boundary without putting bearer tokens in tool arguments, logs, argv, Git, or global Cursor config.
   - Remove static bearer from all non-local-test paths. Prove mint, early renewal, expiry, 401 invalidation, bounded retry, failure, and no-secret diagnostics.

2. **Fail closed on production persistence**
   - Production/stage Gateway startup must require `LINKSKILLS_GATEWAY_STORE=postgres` (or the canonical corrected selector), a valid DSN/SecretRef, migration/readiness probe, and Postgres adapter.
   - In-memory/SQLite stores remain explicit local/test only. Never silently default to memory in production.
   - Correct `deploy/vps/.env.example`, service definitions, runbooks, health/readiness, and packaging tests so documented production launch is durable and restart-safe.

3. **Create the real Librarian queue schema**
   - Add an additive deterministic `lskills.review_queue` migration with correct tenant/actor RLS, roles, lifecycle, idempotency, provenance, retry/dead-letter, retention, and indexes, or bind the adapter to an already approved migrated queue.
   - Never use `tests/helpers/ephemeral_review_queue_ddl.sql` as a live migration.
   - Add it to the ordered hashed manifest and all Platform/Librarian handoffs. Prove fresh+upgrade, wrong actor/org, transaction-context non-leak, concurrency, rollback, and recovery with ephemeral Postgres.

4. **Fix production packaging and mandatory privacy dependencies**
   - Make all required runtime packages explicit and installable: Gateway must require the canonical core/privacy logic; Postgres adapters must include a pinned maintained PostgreSQL driver; Librarian must include its driver; Publisher must have a proper package artifact.
   - Privacy/validation controls must fail startup if unavailable, never silently disable because an optional import fails.
   - Add clean isolated install/build/import/start/package proofs for Gateway, MCP/client proxy, Publisher, Eval Runner, and Librarian.

5. **Enforce the frozen PACI envelope and 15-minute lifetime**
   - Repin from draft behavior to frozen `platform.auth-token-envelope/0.1.0` and exact Platform artifact hashes.
   - Enforce strict unknown-field, array audience, UUID `jti`, JOSE, issuer/audience/service/operation, whole-second cross-field, and zero-skew semantics.
   - Require access-token lifetime not to exceed 900 seconds and reject a token/client response with longer TTL; never let client `expires_in` override the frozen maximum.
   - Run all frozen Platform fixtures and signed adversarial tests, including the independently reproduced 3600-second token rejection.

6. **Authenticated introspection must bind exactly**
   - For `active:true`, require and exactly match issuer, audience, subject, client, credential, runtime binding, token `jti`, times, token type, and required scope/operation. Missing required fields deny; do not condition checks on response truthiness.
   - Outside explicit local-test, startup must fail unless a real `private_key_jwt` assertion signer/SecretRef-backed key provider exists. Remove `StubClientAssertionSigner` from stage/production construction.
   - Prove inactive privacy, wrong/missing binding fields, assertion replay, signer absence, timeout/outage, and cache purge.

7. **Require HTTPS in non-test PACI transport**
   - Discovery, JWKS, token, introspection, and Gateway endpoints must be HTTPS in stage/production.
   - Allow HTTP only for explicit local-test loopback with a clearly named test gate.
   - Reject HTTP production configuration and update tests that currently accept it.

8. **Align every operator artifact**
   - Include migration `000007` and the new review-queue migration in stage/Librarian packets and manifests.
   - Align environment names exactly with code (`JWKS_URI`, `REQUIRED_SERVICE_SCOPES`, `TOKEN_ENDPOINT`, and the canonical private-key file/SecretRef field).
   - Add a machine-validated config contract test so templates/runbooks/service definitions cannot drift from runtime parsing.

9. **Graceful drain and shutdown**
   - Handle SIGTERM and SIGINT, stop intake, enter drain, wait boundedly for in-flight work/buffers, persist retryable state, close database connections, and exit honestly.
   - Add signal/drain/timeout/restart tests without contacting live services.

10. **Evidence hygiene**
   - Fix all `git diff --check origin/development...HEAD` whitespace failures.
   - Correct the seven-class ledger and handoff so local implementation, installable packaging, frozen-contract conformance, stage, canary, and production are separate atomic claims.

## Required proof

Run the full pytest suite, skill-runtime tests, validator/catalog/ownership, frozen PACI fixtures/adversarial tests, project-scoped Cursor MCP token-flow tests, ephemeral Postgres fresh+upgrade+RLS+concurrency+rollback, isolated packaging proofs, graceful shutdown tests, secret scan, and `git diff --check origin/development...HEAD`. Record all failures and reruns.

Commit cohesive changes, push the existing branch, keep PR #22 draft, close the implementation session, and create a dated correction handoff with exact start/code/clean heads, Platform pins/hashes, files, commands, results, residuals, and corrected ledger. Stop for LiNKskills Codex re-verification. Do not self-certify.
