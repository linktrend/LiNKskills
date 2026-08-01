# Cursor Grok 4.5 High — LiNKskills Production IV Correction Wave 3

Continue the existing LiNKskills branch from exact clean HEAD `bae7c36d93b90d558f43ac0b8132ce84658fd443`. Use Cursor Grok 4.5 High and spawn only Grok 4.5 High subagents for bounded parallel lanes. Preserve the durable Cursor HTTP path, additive migration `000009`, distinct introspection principals, certification/idempotency/privacy controls, and all passing tests.

## Lane A — close the review-queue identity bypass

- `PostgresReviewQueueStore.enqueue()` must derive actor and organization exclusively from the authenticated/bound identity context, or reject any supplied item identity that disagrees.
- Never set RLS GUCs from untrusted item fields.
- Add the exact adversarial regression: bound `actor-a/org-a`, submitted `actor-b/org-a` must fail with no row visible to either actor.
- Also cover wrong org, absent bound identity, privileged Librarian/service policy, update/dequeue paths, and transaction/GUC non-leakage.
- Keep the additive database actor+org policy; do not weaken it to compensate for the adapter.

## Lane B — complete operator configuration contracts

- Add `LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS` to the production service definition, production runbook, config fragments/templates, and the operator config-drift test.
- Explain in operator-safe language that this allow-list contains token-minting client IDs and is distinct from the resource server’s introspection assertion client ID.
- Production startup/high-risk operations must fail closed when this required separation is missing or ambiguous.

## Lane C — Platform repin gate

- Platform `83501b11…` failed independent verification. Do not repin to it or invent a future SHA.
- Retain the frozen envelope until Platform Codex certifies a corrected descendant. Prepare deterministic packaged interoperability tooling if helpful.
- A later continuation must repin exact Platform head/package/tarball/schema/fixtures and run the packaged interoperability proof before stage.

Correct the Wave-2 handoff to record exact HEAD `bae7c36d93b90d558f43ac0b8132ce84658fd443` through a dated amendment or new Wave-3 handoff. Run focused tests, full supported-Python pytest, ephemeral Postgres/RLS, config validation, validator/catalog/ownership, packaging, and `git diff --check`. Do not poll CI/Bugbot.

No live migrations, deploy, canary, sibling/global Cursor edits, credentials, PR readiness, merge, promotion, or self-certification. Return a clean pushed HEAD, implementation commit, exact tests, identity-bypass proof, config-contract proof, repin status, and provisional handoff for Skills Codex re-verification. Stop there.
