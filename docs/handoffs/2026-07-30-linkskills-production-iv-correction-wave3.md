# LiNKskills production IV correction wave 3 — provisional handoff

**Status:** `CORRECTION_COMPLETE` for Skills-owned lanes A–B; Lane C **`AWAITING_CODEX_CERTIFIED_PLATFORM_REPIN`**
**Stop for:** LiNKskills Codex re-verification (do not self-certify)
**Executor:** Cursor Local Agent (Grok 4.5 High) + parallel Grok 4.5 High subagents
**Date / time:** 2026-07-30 Asia/Taipei
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**PR:** https://github.com/linktrend/LiNKskills/pull/22 (**draft; do not merge**)
**Wave-3 prompt:** `docs/CURSOR-GROK-PRODUCTION-IV-CORRECTION-WAVE3-2026-07-30.md`

## Exact heads

| Field | SHA |
|---|---|
| Exact start HEAD | `bae7c36d93b90d558f43ac0b8132ce84658fd443` |
| Wave-3 prompt/session commit | `7b1908378b2794c63c4a547b7e2487bf48dd722c` |
| Implementation commit | reported by agent after push |
| Exact clean pushed HEAD | reported by agent after push |

Wave-2 Exact clean HEAD amendment: see dated amendment on
`docs/handoffs/2026-07-30-linkskills-production-iv-correction-wave2.md`
(`bae7c36d93b90d558f43ac0b8132ce84658fd443`).

## Platform repin status (Lane C)

| Field | Value |
|---|---|
| Status | **`AWAITING_CODEX_CERTIFIED_PLATFORM_REPIN`** |
| Failed tip (do not consume) | `83501b11b78b0c5f46a5c5ef23f48de9f1317468` |
| Skills continues against | frozen `platform.auth-token-envelope/0.1.0` / `@linktrend/platform-contracts@0.3.0` (pin HEAD `0455846487d0b8c583859060ba8b4be70e7f0b48`) |
| Packaged interoperability | **not run** (no Codex-certified tip) |
| Prep note | `docs/contracts/LANE-C-PACKAGED-INTEROP-PREP-2026-07-30.md` (non-authoritative) |

## Lanes completed

### A — Review-queue identity bypass closed
- `PostgresReviewQueueStore` derives actor/org **only** from `bind_identity` / `identity()`.
- Item `actor_id`/`org_id` never set RLS GUCs; non-empty disagreement ⇒ `ValueError`.
- Exact adversarial proof: bound `actor-a/org-a` + item `actor-b/org-a` fails; **no row** visible to either actor.
- Also covered: forged org, absent bind, privileged `service_scope=org` still rejects forge, mutations use bound identity, GUC non-leakage retained.
- Additive DB policy `000009` unchanged.

### B — Operator mint-client allow-list contract
- `LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS` in service definition, production runbook, `.env.example`, and operator config-drift test.
- Operator wording: mint allow-list is **distinct** from RS `LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID`.
- Runtime fail-closed already enforced in `paci_authenticator.py` (startup + high-risk writes); docs/tests now match.

### C — Platform synchronization
- No repin; failed tip `83501b11…` not consumed; no invented SHA.

## Local proof

| Suite | Result |
|---|---|
| Focused wave-3 (identity + config + introspection) | **22 passed** |
| Full pytest (supported Python `.venv` 3.14) | **369 passed, 4 skipped, 189 subtests** (~80s) |
| Ephemeral Postgres + packaging | **28 passed** |
| validator / catalog / ownership / skill_runtime | PASS / 34 skills / success / **6 passed** |
| `git diff --check` (working tree + vs `origin/development`) | clean |
| CI / Bugbot | **not polled** |

### Identity-bypass proof (exact)
- `test_review_queue_enqueue_rejects_forged_actor_identity`
- `test_review_queue_enqueue_rejects_forged_org_identity`
- `test_review_queue_enqueue_rejects_absent_bound_identity`
- `test_review_queue_privileged_org_scope_rejects_forged_enqueue`
- `test_review_queue_mutations_use_bound_identity_only`
- Unit: `tests/librarian_domain/test_postgres_identity.py` (6 cases)

### Config-contract proof (exact)
- `tests/config/test_operator_config_contract.py` includes `ENV_PACI_TRUSTED_MINT_CLIENT_IDS`
- `test_operator_artifacts_state_mint_vs_assertion_client_separation`

## Remaining gates

1. Independently **Codex-certified** Platform PACI tip → then Skills Lane C/D repin + packaged interop
2. LiNKskills Codex re-verification of this tip
3. Platform live migrate `000007`–`000009`, stage PACI, canary — not started

## Non-claims

No merge, live migrate, deploy, canary, sibling edits, credentials, PR readiness, promotion, CI/Bugbot poll, Platform repin, or Codex self-certification.
