# Cursor Grok 4.5 High — LiNKskills Production IV Correction Wave 2

Continue the existing LiNKskills branch from exact clean HEAD `61850d942ac2bf053a8a464e199e1a2f72e6fa2a`. Use Cursor Grok 4.5 High. Spawn only Grok 4.5 High subagents and parallelize the bounded lanes below; the primary agent owns integration, final proof, and the handoff.

Preserve the sealed receipt/certification work, idempotency fencing, request-local mutation isolation, immutable release/profile semantics, strict auth envelope verification, production fail-closed intent, and all passing tests.

## Mandatory corrections

### Lane A — durable Cursor canary path

- The production Cursor fragment must use the authenticated HTTP upstream to the durable stage Gateway, or explicitly require stage environment, Postgres store, and DSN before permitting in-process production mode.
- `LINKSKILLS_AUTH_MODE=production` must never silently construct an in-memory Gateway because `LINKSKILLS_ENV`, store, or DSN is missing.
- Fail startup with a safe actionable error rather than falling back.
- Add configuration and end-to-end fragment tests proving the exact production canary path is durable and the local-test path remains explicit.

### Lane B — review-queue actor and organization isolation

- Correct migration `000008` additively with a new migration; do not rewrite applied-history candidates.
- Enforce both actor and organization isolation for review-queue rows according to the plan. A different actor in the same organization must be denied unless an explicit approved Librarian/service policy grants it.
- Replace the current test that treats same-org wrong-actor visibility as success with adversarial denial tests, including wrong actor, wrong org, missing GUC, and privileged Librarian service behavior.

### Lane C — correct introspection principal model

- Separate the resource server’s private-key-JWT assertion client ID from the trusted access-token mint client IDs.
- Validate the introspection response `client_id` against the authorized minting client(s), not against the Gateway’s introspection assertion identity.
- Preserve exact token audience/service/actor/org/binding/credential checks and fail closed on ambiguity.
- Add tests with deliberately different Cursor mint-client and Skills resource-server assertion-client IDs so the old conflation cannot pass.

### Lane D — Platform synchronization gate

- Platform HEAD `39c46680f058d86484fcb24c25c3463deb9488ae` failed independent verification and must not be treated as certified authority.
- Complete lanes A-C against the frozen `platform.auth-token-envelope/0.1.0` contract, then wait for the final independently certified Platform correction head.
- Repin exact Platform head, PACI package/tarball, schema, fixture, and provenance hashes only after that result exists; run direct interoperability tests from the packaged Platform artifact.
- Do not invent or predeclare a final Platform SHA.

## Proof required

Run focused tests, full supported-Python pytest, ephemeral Postgres fresh/upgrade/RLS tests, isolated packaging/import proofs, validator/catalog/ownership checks, configuration-fragment validation, deterministic hashes, and `git diff --check`. Do not poll hosted CI or Bugbot.

## Hard boundaries

- Do not edit Platform, Brain, OpenClaw, global Cursor configuration, or Lisa.
- Do not apply live migrations, deploy, run canaries, create credentials/keys, incur costs, change PR readiness, merge, or promote.
- Do not self-certify.

Finish with a clean pushed branch and provisional handoff for LiNKskills Codex re-verification. Return the exact clean HEAD, implementation commit, changed files, test counts, migration hash, durable canary proof, Platform repin status, remaining gates, and handoff path. Stop there.
