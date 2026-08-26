# PKT-25 provider exact-tree rehearsal

This directory is a preparatory evidence lane. The verifier records source
identity and a deterministic check plan; it does not qualify a release,
contact a provider, configure a consumer, deploy, or prove stage, VPS, E2E, or
production behavior.

## Admission boundary

The receipt must remain `PREPARATORY_ONLY`, with `PKT-24` marked unresolved.
PKT-24 owns the serially integrated catalogue, migration, supersession, and
authoritative-document candidate required before PKT-25 can run against the
actual Phase candidate. The verifier therefore always returns
`admission.admissible: false` and records the external proof classes as false.

## Exact candidate inputs

Bind every future run to all of these values, read from the physical checkout
and never copied from a merge-ref receipt:

1. normalized `origin`;
2. explicit candidate `ref` (never `HEAD` or an unqualified symbolic name);
3. candidate commit and `HEAD^{tree}`;
4. clean-checkout result;
5. provider repository/ref/commit/tree and the exact owned paths.

The current protected baseline is commit
`667dbfd817114ec6761a6c1a44c129391d2111ac`, tree
`e894accdd4c9e86645acf5a928c2f1947fd322a7`, on
`refs/remotes/origin/development`. It is a baseline binding, not a PKT-25
candidate-pass claim. The verifier reads that identity from the physical
checkout (`git symbolic-ref HEAD` plus `HEAD` commit/tree) and never from
`@{upstream}` or a copied merge-ref receipt. Credential-bearing origin URLs
are stripped before they are stored.

## Offline rehearsal command

`offline_provider_rehearsal.py` runs an in-process loopback fake. It exercises
bounded catalogue discovery, exact package digest verification, disconnect
handling, redacted buffering, and idempotent replay. It never opens a socket
or contacts a provider. The resulting receipt is `LOCAL_ONLY` and binds the
source checkout, package bytes, manifest digest, and result digest. A passing
local rehearsal cannot clear PKT-24, consumer, hosted, VPS, E2E, or production
gates.

```bash
python3 evidence/governed-skill-expansion/provider/offline_provider_rehearsal.py \
  --output /tmp/pkt25-offline-receipt.json
```

`package-receipt.template.json` defines the required immutable package and
receipt fields. `migration-rollback-recovery.template.json` is a handoff
template only: it does not apply SQL, mutate a shared database, rotate a
credential, or perform consumer/VPS recovery.

## Required check matrix

Each check must be executed on the same exact candidate and recorded with its
command, exit status, and output digest. `NOT_RUN`, `HOLD`, or an unbound
receipt is a fail-closed result.

| Check | Required command/evidence | Proof class |
| --- | --- | --- |
| scoped packet checks and negative probes | focused PKT checks plus relevant rejection/privacy probes | source |
| full repository validation | `python3 -m unittest discover -s tests -p 'test_*.py' -v` | source |
| catalogue check | `python3 scripts/build-catalog-index.py --check` | source |
| isolated package tests | package-level test command appropriate to the candidate | source |
| secret scan | repository secret scanner with exact candidate tree binding | source |
| privacy scan | raw-private-data and telemetry/privacy negative tests | source |
| exact diff audit | `git diff --check` and immutable base-to-candidate path comparison | source |
| ancestry audit | `git merge-base --is-ancestor` for every issue commit and the candidate | source |

The check plan is deliberately not a claim that these commands have run.
`verify_exact_tree.py` can read local Git identity and emits a non-zero exit
status while the dependency or any required check remains unresolved.

## Owned-path rule

The implementation/evidence paths in this lane are under
`evidence/governed-skill-expansion/provider/`. The generated
`.github/linktrend-secret-scan-fixtures.json` output is the sole allowed
scope exception and must pass generated-output closure and the exact candidate
tree secret scan. Catalogue, docs, skills, packages, migrations, deployment,
release, configuration, and PKT-22/23/24 paths remain owned-path leaks.
