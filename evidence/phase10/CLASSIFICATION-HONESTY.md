# Classification honesty rules (LiNKskills)

**Authority:** ADR 0006 (execution-profile certification), ADR 0009 (confined executor isolation), `packages/core/linkskills_core/certification.py`  
**Ledger:** `evidence/phase10/skill-classification-draft.json`  
**Updated:** 2026-07-30

## Purpose

Keep the catalog classification ledger honest. Local unit tests, fake hosts, macOS dry-runs, and legacy receipts that omit proven isolation must never be recorded as live usable/certified promotions.

## Allowed classification states

| State | Meaning | Promotion gate |
|---|---|---|
| `draft` | Default. Source may exist; no sealed live certifying evidence | Stay until evidence |
| `eval_pending` | Submitted to real Eval Runner on a certifiable host; awaiting sealed pass | Requires queued/running sealed eval, not prompt-only |
| `usable` | Sealed pass with certifying receipts + publication path | `network_isolation == "denied"` on sealed receipts |
| `deprecated` | Explicit lifecycle decision with migration guidance | Lifecycle proposal + evidence |
| `retired` | Explicit end-of-life | Lifecycle proposal + migration |

No other informal states (`certified_local`, `almost_usable`, macOS “certified”) are valid in this ledger.

## Certifying evidence requirements

A skill may leave `draft` toward `usable` only when **all** of the following are true and cited by path in the ledger:

1. **Sealed executor receipt** from the Eval Runner issuer path (`sealed_executor_receipt`).
2. **`network_isolation == "denied"`** on every certifying receipt (ADR 0009).
3. Receipts bind suite hash, immutable skill release hash, execution-profile hash, toolchain, and collected evidence hashes.
4. Host is certifiable: today **Linux `bwrap`** (or an already approved container/VM path). **macOS is not certifiable** when isolation is `unproven` / probe-failed.
5. Evidence paths are in-repo (or Platform-owned immutable stage evidence refs once supplied). Empty `sealed_live_receipt_evidence` means **no promotion**.

## Explicit non-evidence

Do **not** treat any of the following as sealed live certification:

- Unit/conformance tests that mint synthetic receipts with `network_isolation="denied"` (test-only).
- `LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven` runs (`unproven` stamps).
- Prompt-only scoring, suite-authored `observed_output` / `fixture_output`.
- Legacy `evidence/phase3/canary-echo-cli.json` — macOS, missing `network_isolation`, and not a catalog skill; its historical `certified: true` flag is superseded by ADR 0009.
- Fake Gateway/MCP/Librarian host proofs.
- Cursor canary stages 1–2 fake/contract evidence (`evidence/phase7/cursor-canary-status.json`).

## Host honesty fields (ledger top-level)

| Field | Required value until proven otherwise |
|---|---|
| `live_certification` | `"not performed"` (or a dated Platform-supplied stage receipt ref) |
| `macos_certifiable` | `false` |
| `linux_bwrap_required` | `true` |
| `updated_at` | ISO-8601 UTC when the ledger changes |

## macOS / Linux

- **macOS:** may run local dry-runs and unit tests; must stamp `unproven`/`unavailable` when isolation cannot be proven; **must not** claim usable/certified.
- **Linux:** certifiable only with proven path-allowlisted `bwrap --unshare-net` (no `--ro-bind / /`). Production/canary hosts needing certifiable receipts must provide this.

## Deprecated / retired

Entries move to `deprecated` or `retired` only with an explicit lifecycle rationale (overlap, supersession, safety). Absence of evidence is **`draft`**, not deprecated.

## Update discipline

1. Edit `skill-classification-draft.json` with per-skill `classification` and `sealed_live_receipt_evidence` paths.
2. Refresh top-level honesty fields and `counts`.
3. Never invent live stage endpoints, JWKS URLs, or canary start dates.
4. Do not start multi-day canaries from a classification update alone.
