# Hosted sealed-evaluator contract (ED-03 qualification)

**Status:** contract-only — **not** a live qualification, **not** a `usable` certification
**Packet:** ED-03 hosted executor admission
**Local privileged script:** `scripts/run-sealed-linux-certify.sh` remains **workstation-only**

## Separation

| Path | What it is | What it is not |
|---|---|---|
| `scripts/run-sealed-linux-certify.sh` | Local privileged Docker + `bwrap` on an operator workstation | A Server01/VPS/production executor. Must never be copied there. Must never be given production issuer keys. |
| Local `--local-non-promoting` | Pipeline smoke; `draft` / `eval_pending` only | Promotion, sealed release evidence, hosted admission |
| `validate_hosted_sealed_evaluator_contract` | Fail-closed **admission** for a *future* hosted Linux executor | A credential, a Docker grant on Server01, a live provider/consumer claim, or fabricated `usable` evidence |

Passing the hosted contract means a future executor **may be considered** only when every pin below is present. It does **not** certify skills, publish releases, or apply stage/prod.

## Required admission fields

Schema id: `linkskills.hosted-sealed-evaluator/0.1.0`

| Field | Rule |
|---|---|
| `executor_kind` | Must be `hosted` |
| `image` | Digest-pinned Linux image `name@sha256:<64 hex>` — floating tags fail closed |
| `issuer_injection` | `process-env-name-only` (name-only process env). No argv `KEY=value`, no disk secret files, no key material in the contract document |
| `network_isolation` | `denied` |
| `network_isolation_proof` | `bwrap-unshare-net` or `linux-network-namespace-denied` only (`allow_unproven` / macOS sandbox is not admitted) |
| `source_commit` | Exact 40-hex git commit of the admitted source identity |
| `source_tree` | Exact 40-hex git tree of that commit |
| `source_tree_sha256` | 64-hex governed-input digest (catalog provenance) |
| `artifact_retention.max_bytes` | `> 0` and `≤ 33554432` (32 MiB) |
| `artifact_retention.max_age_hours` | `> 0` and `≤ 48` |
| `artifact_retention.allowed_path_prefixes` | Only under `evidence/end-to-end-delivery/ed-03/`, `evidence/tmp/hosted-sealed/`, or `/tmp/linkskills-hosted-sealed/` |
| `qualification_claim` / `authorizes_usable` | Must not assert `usable`, `certified`, `live`, or `production`. Contract admission is not certification. |

## Hard refusals

- `privileged_docker` / `--privileged` on the hosted path
- Transfer of `scripts/run-sealed-linux-certify.sh` to Server01, VPS, or a hosted executor
- `LINKSKILLS_SEALED_TARGET` in `{server01, vps, production, prod, stage-vps, shared-runtime}` for the local script
- `LINKSKILLS_USE_PRODUCTION_ISSUER` on the local privileged script
- Repository-visible local HMAC issuer key on the hosted path
- Embedded secrets/credentials in the contract payload
- Writes under `evidence/phase10/sealed/` from the hosted contract (that directory is the local sealed-release evidence tree)
- Catalog overlay treating a hosted-contract JSON document as sealed live receipt evidence

## Local non-promoting (preserved)

```bash
./scripts/run-sealed-linux-certify.sh --local-non-promoting --skill canary-echo
```

This mode is unchanged: documented local key + floating tag allowed; outcomes stay `draft` / `eval_pending`; no sealed release evidence write.

## Future executor (out of this issue)

A later hosted implementation must inject issuer material from GSM into process env (name-only), prove `network_isolation=denied` on the digest-pinned image, bind the exact source commit/tree, retain artifacts only inside the bounds above, and fail closed on any missing pin. This issue does **not** deploy that executor, grant Docker on Server01, or mint a usable catalog row.
