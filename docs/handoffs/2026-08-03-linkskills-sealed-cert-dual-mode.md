# Handoff — Sealed-cert issuer/image dual-mode (launch-blocking audit)

**Date:** 2026-08-03
**Branch:** `dev/cloudcursor/skills-stage-certification`
**Tip SHA:** `7d0f7d133a7e7ebcaa67320aeefa0a6d3dd22dc0`
**Verdict:** **PASS** for local dual-mode sealed-cert remediation; **HOLD** for GSM/stage/shared apply

## Launch-blocking gap corrected

`scripts/run-sealed-linux-certify.sh` no longer defaults to floating `python:3.12-slim` +
repository-visible HMAC `linkskills-local-eval-runner-issuer-key-not-for-production` for
promoting artifacts.

### Mode A — release/promoting (default)

- Requires externally supplied `LINKSKILLS_EVAL_RUNNER_ISSUER_KEY` (no fallback).
- Rejects the repository-visible local HMAC key.
- Requires digest-pinned `LINKSKILLS_SEALED_CERT_IMAGE` (`name@sha256:<64 hex>`).
- Records `issuer_id` + image digest in sealed evidence host metadata.
- Never logs the key.
- Fails closed before Docker mutation when missing/unpinned.

### Mode B — local non-promoting (`--local-non-promoting`)

- May use documented local key + floating image tag.
- Forces catalog outcomes to `draft` / `eval_pending`.
- Does not write `evidence/phase10/sealed/` release evidence.
- Skips ledger/catalog usable promotion.

### Overlay / promotion honesty

`verify_sealed_live_evidence` ignores the local-dev key: public-key-signed receipts cannot
authorize `usable`.

### canary-echo side-effect claim

Reconciled: no durable shared/repo/network mutation; workspace-scoped tool writes only inside
ephemeral sealed workspace; `execution_ledger.jsonl` telemetry is mandatory/expected.

## Trust binding (post re-seal)

| Constant | Value |
|---|---|
| text-echo source/tool hash | `6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0` |
| skill_release_hash | `skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb` |
| profile_hash | `4e146372eb9e0e07c09ce1cd20d6bda3199d7847637c2e93bbf35b2bdde0a4f9` |
| suite_hash | `8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662` |
| sealed_evidence_sha256 | `f5b7a8517130ee55e011ac93408f3c042f3e0efb77176344413ab7a3e8888f72` |

000010 regenerated and bound only to externally signed promoting evidence.

## Counts

| Metric | Value |
|---|---|
| Catalog skills | 35 |
| `usable` | 1 (`canary-echo`) when promoting key present |
| `draft` | 34 |

## Residual HOLD

- Production issuer key still GSM process-only (not configured in this session).
- Stage DB apply still Platform-owned (PREFLIGHT B1–B5).
- No live Lisa / VPS / shared Gateway mutation.
- Local rebuild without promoting key fail-closes canary to draft (honest).
