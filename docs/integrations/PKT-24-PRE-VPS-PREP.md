# PKT-24 pre-VPS integration preparation

- **Packet:** PKT-24 — catalogue generation, supersession mappings, and documentation integration
- **Lane:** bounded pre-VPS preparation (integration documentation only)
- **Prepared:** 2026-08-25 (Asia/Taipei)
- **Authoring repository:** LiNKskills
- **Status:** **PREPARATORY_ONLY / HOLD**
- **Dependencies:** PKT-22 and PKT-23 are not independently cleared; PKT-24 is not complete
- **Scope of this lane:** `docs/integrations/` only

This document turns the existing integration handoffs into a reviewable rehearsal package. It
does not generate or alter the catalogue, apply migrations, configure a consumer, publish a
release, provision a credential, connect to a provider, deploy to a VPS, or qualify production.
All live/provider/stage/VPS/production claims below are explicitly **NOT_PROVEN**.

## 1. Non-negotiable boundaries

| Surface | LiNKskills preparation | Live authority / proof owner | Current state |
|---|---|---|---|
| Skill source, migration bytes, and contract docs | Author and validate source-owned material | LiNKskills | Source bytes available; this lane does not change them |
| Identity, credentials, JWKS, grants, and shared database migration apply | Supply names, placeholders, hashes, and checks | LiNKplatform | **NOT_PROVEN / HOLD** |
| OpenClaw/Lisa profile, MCP wiring, buffers, and consumer rollback | Receive this handoff and apply in its own repo | OpenClaw Prime | **NOT_PROVEN / HOLD** |
| Deterministic polling, schedules, retry, and audit hooks | Consume the contract and prove in its own repo | LiNKautowork | **NOT_PROVEN / HOLD** |
| Host checkout, process supervisor, secret-file injection, deploy, and rollback | Provide rehearsal checklist only | VPS/deployment owner | **NOT_PROVEN / HOLD** |
| Cross-repo/source-to-runtime and final qualification | Independently inspect exact identities and evidence | Final verifier / Codex | **NOT_PROVEN / HOLD** |

The Skills repository does not own governance, entitlements, leases, kill-switches, the shared
Platform ledger, a consumer's authoritative profile, or deployment authority. A local test,
source hash, fake token, or provider candidate is not stage, VPS, or production proof.

## 2. Configuration-template contract (placeholders only)

The following is a contract for a future owner to materialise in its own environment. It is not
a request to add a config file to this repository. Values beginning with `<` are required
placeholders and must remain uncommitted until the named owner supplies them through its approved
secret/configuration channel.

### 2.1 Skills Gateway / PACI consumer template

```text
LINKSKILLS_ENV=<local-test|stage|production>
LINKSKILLS_AUTH_MODE=<local-test|production>
LINKSKILLS_CANARY=<0|1>
LINKSKILLS_MCP_UPSTREAM=<http|in-process>
GATEWAY_URL=<https://skills-gateway.<stage-or-prod-domain>>
LINKSKILLS_PLATFORM_AUTHENTICATOR=<platform-approved-authenticator-module>
LINKSKILLS_PACI_CLIENT_ID=<platform-issued-skills-client-id>
LINKSKILLS_PACI_TOKEN_ENDPOINT=<https://platform.<env-domain>/oauth/token>
LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE=<absolute-secretref-injected-pem-path>
LINKSKILLS_PACI_CLIENT_KID=<registered-es256-kid>
LINKSKILLS_PACI_SCOPE=<least-privilege-skills-scopes>
LINKSKILLS_PACI_RESOURCE_AUDIENCE=<skills-only-resource-audience>
LINKSKILLS_GATEWAY_DSN=<secretref-injected-dsn>
```

Required refusal rules:

1. Outside explicit local-test loopback, `GATEWAY_URL` and the PACI endpoint must be HTTPS.
2. The private key is a file path only; its PEM bytes must never appear in Git, arguments, MCP
   environment values, logs, fixtures, receipts, or chat.
3. Skills client identity, audience, scope, issuer, and key must not be reused for Brain or
   OpenClaw. Platform owns registration and issuance.
4. Production/canary uses `LINKSKILLS_AUTH_MODE=production`, `LINKSKILLS_CANARY=1`, and durable
   HTTP Gateway. Static bearers are local-test only and are refused for a canary.
5. No refresh token is expected. Access TTL must be at most 900 seconds; renew before 20% of TTL
   remains, invalidate on 401, and use only a bounded retry.
6. Production must fail closed when the authenticator, endpoint, DSN, secret file, audience, or
   required claims are absent or inconsistent. Do not silently construct an in-memory Gateway.

### 2.2 OpenClaw / Lisa consumer handoff template

```yaml
skills_provider:
  repository: LiNKskills
  release_id: <immutable-published-release-id>
  release_sha256: <release-bundle-sha256>
  gateway_url: <https-skills-gateway-url>
  resource_audience: <skills-only-resource-audience>
  auth_secret_ref: <platform-secret-reference-not-a-secret-value>
  live_enabled: false
  proof_ref: <openclaw-owned-consumer-proof-ref>
```

`live_enabled` must remain `false` until OpenClaw Prime has a consumer-owned exact pin,
credential-binding proof, safe profile diff, read-only discovery evidence, and rollback receipt.
This Skills document does not edit or imply the authoritative Lisa profile.

### 2.3 Secret boundary

| Material | May appear in this package? | Owner / handling |
|---|---|---|
| Environment variable names and placeholder labels | Yes | Contract documentation |
| Public commit/tree/content hashes | Yes | Reproducibility and review |
| Private keys, access/refresh tokens, DSNs, cookies, raw JWTs | **No** | GSM/SecretRef and owning runtime only |
| Provider credentials or vendor payloads | **No** | LiNKplatform/provider owner; preserve only immutable public digests |
| Real customer, lead, trading, Brain transcript, or Lisa data | **No** | Never use for rehearsal |

## 3. Migration manifest and Platform-owned checklist

The table is a source-side hash manifest. It is not an apply receipt. Every live apply, backup,
restore rehearsal, and schema verification must be performed and recorded by LiNKplatform. The
sequence is cumulative and must stop on a missing prerequisite, hash mismatch, failed backup, or
failed verification. Down files are recovery inputs, not an instruction to run destructive SQL
from a Skills session.

| Order | Up migration | SHA-256 | Companion down / status |
|---:|---|---|---|
| 2 | `20260715_000002_lskills_catalog_core.sql` | `4991dd628cc501a1013a4d7c3d8f859274e62ff847e768f106b0e3c2b89d8414` | Existing prerequisite |
| 3 | `20260715_000003_lskills_catalog_seed.sql` | `5e8f58a7159ad09f0c6389e12060c6a9cc76ff73dcfc2397ddea256d47a75e82` | Existing prerequisite |
| 4 | `20260718_000004_lskills_postgrest_exposure.sql` | `4220d70b626313f572a38720958fb78550b3b89c0efab5366a449d33c0b22ca0` | Existing prerequisite |
| 5 | `20260727_000005_lskills_registry_foundation.sql` | `36081765032f21dfd2dcca223035555e1e54b71298874235def8e0362c55c4ed` | Additive registry foundation |
| 6 | `20260728_000006_lskills_rls_actor_org_scope.sql` | `12c2e45e94fd9216a5857ce53ce299a953dc2ee869f89bcdb392857133df763d` | Actor/org RLS prerequisite |
| 7 | `20260730_000007_lskills_gateway_persistence.sql` | `c26d1c55d9f87e242fe1e225fd4240cd911a5e0315d88500417d491689596222` | Gateway persistence |
| 8 | `20260730_000008_lskills_review_queue.sql` | `0d5cf1f6abf62bddffc2e494bd8fb7faabe5aceb44266d446bb71f1209f43bab` | Review queue |
| 9 | `20260730_000009_lskills_review_queue_actor_isolation.sql` | `acd0a1dbf81697d4e278ed4cdfa11d4b410b383420e02e6105940f578b6b6467` | Actor-isolation upgrade |
| 10 | `20260803_000010_lskills_canary_echo_usable_seed.sql` | `5e391f4845984dbf83724b3ac931a879f774f91014fb46ced89154145df9f059` | Additive canary seed; still stage-blocked |
| 11 | `20260804_000011_lskills_gateway_role_rls_contract.sql` | `0a8c56ee8ac2b3368d2a0ea8f6cc98719ccbc852d884dc34bc0143d5c7984a73` | Gateway role/RLS contract |
| 12 | `20260824_000012_lskills_external_collection_lifecycle.sql` | `51236e86c938e7bad8717f94949ccef4bd6ff1d4d1903796abccfbde9f819515` | PKT-03/ISS-03 package; dependency unresolved, **HOLD** |

Companion down hashes are retained for the packages that provide them: `000010` down
`3b48c7f284ae902d6dd97d86dee5f7ba222d04d7900335bd3b3abb9681a2ef5e`, `000011` down
`b538241ef3c95af5e1f51a4781c7600644365720343016d41f15a935e209af89`, and `000012` down
`68090475b40675d2597e28a28733cb439828a6e69c1346bf5c69731eb88ff343`. The earlier registry
manifest's eight-file package remains the historical base; this table records the current source
bytes without claiming that all rows are one approved live bundle.

### Platform apply checklist (must be completed outside this repository)

- [ ] Confirm the exact Skills source commit/tree and recompute every hash above.
- [ ] Confirm Platform foundation, roles, prior ordered migrations, and target environment identity.
- [ ] Create a pre-apply backup receipt with checksum, retention, roles/grants, and RLS coverage.
- [ ] Complete a restore dry-run on a disposable/non-shared target and retain verification output.
- [ ] Obtain separate Platform review and apply receipts; never infer them from local tests.
- [ ] Apply only the approved ordered subset; `000012` requires its PKT-03 dependency decision.
- [ ] Run table, RLS, role, policy, and catalog-floor verification SQL from the owned migration notes.
- [ ] Record a forward-fix or exact package rollback plan before any shared apply.
- [ ] Keep stage/VPS/production status **NOT_PROVEN** until the final verifier accepts immutable
  Platform evidence bound to this source pin.

## 4. Source, local, and offline rehearsal

These rehearsals prove source integrity and fail-closed behavior only. They must not contact a
live provider, shared Supabase, OpenClaw host, VPS, or production endpoint.

### 4.1 Source rehearsal (Skills-owned)

```bash
git fetch origin development
git ls-remote origin refs/heads/development
git rev-parse HEAD HEAD^{tree}
find supabase/migrations -maxdepth 1 -type f -name '*.sql' -print | sort
sha256sum supabase/migrations/*.sql
git diff --check
```

Expected evidence: exact remote/protected base, exact candidate checkout identity, a hash table
matching this document for the selected ordered package, no secrets, and no paths outside the
lane. Hash or ancestry mismatch is a hard stop.

### 4.2 Local contract rehearsal (no live dependencies)

```bash
python3 -m json.tool docs/integrations/PKT-24-PRE-VPS-RECEIPT.json >/dev/null
python3 scripts/build-catalog-index.py --check
python3 validator.py --repo-root . --scan-all
python3 scripts/gitops/secret_scan.py --repo .
git diff --check
```

Expected evidence: JSON parses; the pre-existing catalog and skill packages validate; the secret
scanner reports no real secret; diff check is clean. These results do not prove provider,
Platform, stage, consumer, VPS, E2E, or production status.

### 4.3 Offline consumer rehearsal (OpenClaw/LiNKautowork-owned)

Use only redacted fixtures with a loopback fake Gateway and an explicit `local-test` mode:

1. Load the placeholder template without replacing it with a real secret.
2. Verify startup refuses missing endpoint, audience, credential file, unsupported issuer, and
   static bearer under canary mode.
3. Exercise read-only `skills_list` / exact-release discovery against the loopback fake.
4. Disconnect the fake Gateway; verify bounded retry, redacted offline buffering, stable event
   IDs, and no activation or pointer change.
5. Replay the same event; verify idempotent handling and inspect logs for tokens, keys, DSNs, or
   raw payloads.
6. Restore the fake endpoint; flush only redacted fixtures and capture a deterministic receipt.

Expected evidence belongs to the executing owner and must bind fixture digest, consumer commit,
profile/config digest, test command, event IDs, redaction result, and rollback result. A fake
rehearsal is **LOCAL_ONLY** and cannot clear the stage/VPS/provider gates.

## 5. Rollback, forward-fix, and recovery

### Source/documentation rollback

- Revert the one integration checkpoint or restore the prior exact qualified documentation
  pointer. Do not rewrite an immutable release or amend a published migration.
- Re-run `git diff --check`, focused JSON/markdown checks, catalog check, validator, and secret
  scan after the revert.
- Leave the live status markers and external HOLDs intact.

### Migration rollback / forward-fix (LiNKplatform only)

- Stop on a failed preflight, backup, restore dry-run, hash, prerequisite, or verification check.
- For a reversible additive defect, use the exact reviewed companion down package on a disposable
  target first; never drop `lskills` wholesale or remove unrelated release/vendor bytes.
- For an applied defect or partial state, prefer a new additive forward-fix migration with a new
  hash and Platform review. Re-run verification before declaring recovery.
- Platform owns transaction, backup, apply, role/grant, RLS, receipt, and restore evidence.

### Consumer / VPS recovery (OpenClaw and deployment owner)

- Disable the new consumer profile and restore the prior immutable release/config pin.
- Stop the process before changing secret-file bindings; do not rotate or expose Platform
  credentials from LiNKskills.
- Restore the prior host release retained by the deployment owner, verify health/readiness and
  read-only discovery, then retain a recovery receipt.
- If the exact prior pin or rollback receipt is absent, remain **HOLD**; do not improvise a
  latest/native/fallback release.

## 6. External-dependency matrix

| Dependency | Required input / action | Evidence that would clear the hold | Current status |
|---|---|---|---|
| LiNKplatform | Frozen auth contract, Skills-only client/JWKS/grants, target identity, backup/restore, ordered migration apply, schema/RLS/role receipts | Platform-owned immutable receipts tied to Skills source SHA/tree and manifest hashes | **NOT_PROVEN / HOLD** |
| OpenClaw Prime | Consumer adapter, Lisa profile diff, exact release pin, PACI binding, read-only discovery, offline/retry and rollback proof | OpenClaw-owned commit/config/evidence with no shared-profile mutation from Skills | **NOT_PROVEN / HOLD** |
| LiNKautowork | Deterministic polling/schedule, idempotency, retry/dead-letter, audit and no activation without receipts | Autowork-owned run receipt bound to exact inputs and Platform receipt IDs | **NOT_PROVEN / HOLD** |
| VPS/deployment owner | Host identity, checkout SHA/tree, secret-file injection, supervisor, deployment/rollback and endpoint checks | Deployment receipt with exact release, prior release, health/readiness, and rollback retention | **NOT_PROVEN / HOLD** |
| Final verifier / Codex | Reconcile PKT-22/23 dependencies, source/provider/consumer/Platform/VPS proof classes, scope and receipt truth | Independent ACCEPT with exact identities; otherwise correction packet/HOLD | **NOT_PROVEN / HOLD** |

No dependency row may be converted to “ready” by a Skills-local test, a copied narrative, a
provider candidate SHA, a merge receipt, or a successful source build.

## 7. Exit criteria for a later PKT-24 execution lane

This preparation is not an exit approval. A future, separately authorized PKT-24 lane must at
minimum reconcile PKT-22 and PKT-23, decide the `000012`/PKT-03 dependency, generate the
catalogue and supersession mappings in their owned paths, and obtain independent review of the
documentation and migration package. Only then can PKT-25 exact-tree verification begin. No
step here bypasses PKT-23 or PKT-22, and none authorizes provider access, consumer activation,
live migration, VPS deployment, or production release.
