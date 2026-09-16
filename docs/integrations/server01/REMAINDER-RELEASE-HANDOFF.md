# Remainder Server01 release / activation handoff (nonsecret)

**Status:** `SOURCE_ONLY_NOT_DEPLOYED`. Do not deploy, publish live, apply migrations, or access secrets from this document.

**Admitted Skills source (issue 374 remainder packet):** governed inputs commit `e591f8880dde0e65a935618b235328b03629f7a1`. Catalog `git_sha` is that ancestor (not the catalog-embedding tip). Starting protected development was `b53d3588974dfa7589d5d45a30cb8824337099ba` / tree `e4397f801e72a570a2159c76dfc3e5fb06df83ee`.

Successor five-release production path remains issue 372 / `docs/handoffs/2026-09-15-successor-release.md`. This packet adds the remaining 54 source qualification inputs. Target after Server01: **59** immutable production releases.

## 1. Artifact identity

1. Retrieve `linkskills-server01-<exact commit>` from GitHub Actions.
2. Verify archive checksums and image labels against `source.json`.
3. Retain a detached signature for the exact image. A checksum is not a signature.
4. Retain the prior working image/configuration and a recoverable database backup.

## 2. Migrations (Platform/Server01 apply only)

Apply in order, matching on-disk SHA-256:

1. Existing production-store package `packages/persistence/MIGRATION-MANIFEST.json` (000002–000013).
2. Successor additive `supabase/migrations/20260915031801_lskills_provider_v2_runtime.sql` SHA-256 `1262ad8200130d7127407d659fc0d9ddfdc5aacba164aab9fd8ad64ccdd914e1`.

Do not rewrite previous SQL. Runtime SELECT-only on publication/bindings; receipts RLS by actor/org.

## 3. Hosted sealed qualification of the 54

Do **not** use `./scripts/run-sealed-linux-certify.sh` (workstation privileged Docker).

Run the evaluator image with no network and without privileged Docker. Inject `LINKTREND_SKILLS_PROD_EVAL_RUNNER_ISSUER_KEY` via the approved process environment route plus immutable SecretRef/version/issuer identity and `LINKSKILLS_SEALED_CERT_IMAGE=<tag>@sha256:<digest>`.

```text
qualify --package /tmp/linkskills-hosted-sealed/package.json
```

Bounded writable evidence mount. Bubblewrap must deny case networking. Inability to isolate is a technical failure. Keep five representative families per skill. Do not reuse five-release evidence identities for the 54.

## 4. Publish without activating consumers

```text
python3 /opt/linkskills/scripts/provider_release.py publish --package <path> --expected-commit <accepted image source commit>
```

Publisher uses `LINKSKILLS_PUBLISHER_DATABASE_URL`. Publication does not enable `provider_bindings`.

## 5. Disabled consumer bindings

Templates: `configs/consumer-activation/remainder-provider-bindings.template.json`. Fill org/actor/runtime UUIDs from Platform owner after identity registration. `enabled=false`. Skill retrieval must not create capability grants.

OpenClaw Lisa/David/Eric/Sara/Jane PACI names are catalog HOLDs in Platform's production-identity runbook. Do not invent IDs.

## 6. Rollback identity

Revert the runtime image/config to the retained five-release successor. Preserve new tables and qualification evidence. Disable bindings independently. Publisher may revoke new releases via lifecycle without changing bytes.

## 7. Cloud worker evidence class

This cloud worker did **not** execute the hosted sealed evaluator (no digest-pinned evaluator image, no issuer injection, no non-privileged isolation proof). Source confined drivers are `source_executable_not_production`.
