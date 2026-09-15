# Delivery modes (managed-core GitOps)

**Status:** Binding for managed-core packaging and Review Packager / Integrator behavior.
**Package:** IDE Development managed-core (consumer-installable doctrine + scripts).
**Related:** `docs/AUTONOMOUS-GIT-OPERATIONS.md`, `docs/adr/0003-autonomous-ship-pull-promote.md`, `core/github/CI-GATE-CONTRACTS.md`, `docs/contracts/AGENT-COMPLETION.md`.
**Schema:** `core/managed-core/schemas/delivery-modes.schema.json`

## Purpose

Define **configurable generic delivery modes** for how independently accepted Issue work enters `development`. Modes are product-agnostic. Consumers select a mode; they do not invent product-specific GitOps.

## Modes

| Mode id | Default? | Integration shape |
|---|---|---|
| `issue-pr` | **Yes** (preserve existing generic behavior) | Each review-ready work branch may receive its own draft PR into `development` (current Packager discover behavior). |
| `phase-integration` | Opt-in via config | Frequent Issue **checkpoints** (commit+push only). Independently accepted exact Issue SHAs are included on a **Phase branch**. Packager opens **one Phase PR** into `development` for that Phase head. |

Checkpoint pushes **never** open a PR and **never** request Bugbot, in either mode.

## Phase integration lifecycle

1. **Issue checkpoint:** Implementer commits and pushes on `issue/<id>-<slug>`. No PR. No Bugbot.
2. **Independent Issue acceptance:** Exact tip SHA receives successful `Linktrend Review Ready` (or equivalent acceptance record). Later commits invalidate acceptance for the new tip.
3. **Phase inclusion:** Accepted Issue SHAs are merged/cherry-picked onto `phase/<slug>` (or another configured Phase branch prefix). Machine-readable Phase records list each accepted Issue SHA and prove inclusion. The Packager commits `.linktrend/phase-delivery-record.json` onto the Phase tip as a single-parent identity-binding commit after isolated assembly. `headSha` / `gitTree` name the assembled package commit (an ancestor of the tip), never the self-referential embedding commit that contains this JSON. The Phase PR head and isolated handoff `headCommit` / `gitTree` name the identity-binding tip that protected integration checks out.
4. **Phase PR:** After all required accepted Issue SHAs are included, the Phase tip is marked review-ready through the same trusted completion / App-publisher path used for Issue tips (exact SHA; configured `phase/<slug>` is App-eligible without weakening `issue/<number>-<slug>` safeguards). Review Packager opens **one** draft PR only after validating that Phase delivery record and inclusion evidence: `phase/*` → `development`.
5. **Named gates:** `fast-gate` (then Bugbot when required), Integrator merge, `staging-gate`, and `release-gate` evaluate the **exact PR head SHA**. Missing, empty/zero SHA, wrong SHA, stale event head, skipped/neutral (unless explicitly allowed), or failed checks are **non-success**.

## Risk-based Issue PR exceptions

Under `phase-integration`, an Issue-level PR into `development` is allowed **only** when an explicit risk classification is declared:

- `security`
- `authentication`
- `database_migration`
- `infrastructure`
- `major_shared_api`
- `unusually_large_scope`
- `cross_phase_impact`

Declare the exception with a committed file on the Issue tip:

```json
{
  "schemaVersion": 1,
  "riskClass": "security",
  "reason": "short human-readable justification"
}
```

Path: `.linktrend/issue-pr-exception.json`

Without a valid exception, Packager must **not** open an Issue PR in `phase-integration` mode even when the tip is review-ready (acceptance still stands for Phase inclusion).

Under `issue-pr` mode, risk exceptions are unused; normal Packager Issue PR behavior remains.

## Machine-readable Phase record

Authorized integration tooling writes / updates a Phase delivery record (fixture and live outputs) with at least:

| Field | Meaning |
|---|---|
| `deliveryMode` | `phase-integration` |
| `phaseBranch` | Phase branch name |
| `baseSha` | Integration base (usually `development` tip at Phase open) |
| `headSha` | Exact assembled package commit (parent of the identity-binding tip). Must not equal the commit that embeds this file. |
| `gitTree` | Tree of that assembled package commit, not the identity-binding tree |
| `mergeSha` | Merge commit SHA after Integrator merge, else `null` |
| `phasePr` | `{ number, url, base }` when a Phase PR exists (isolated/PR overlay; may be `null` in the committed blob before GitHub identity exists) |
| `acceptedIssues[]` | `{ branch, sha, accepted, included }` for each required Issue |
| `namedGateEvidence` | Gate id, assembled package SHA, status, per-check outcomes |
| `riskExceptionIssuePrs[]` | Optional Issue PRs opened under explicit risk classes |

Path on the Phase tip: `.linktrend/phase-delivery-record.json` (gitignore exception; other `.linktrend/*` state stays local).

Schema: `core/managed-core/schemas/delivery-modes.schema.json` (`phaseDeliveryRecord`) and `phase-record.schema.json`.

Temporary merge assembly stays in an isolated worktree. Coordinator handoff/provenance for the **pushed tip** is written under the git common directory and must match the remote `phase/*` SHA/tree. A later head invalidates that handoff.

Packager discovery **must** load the committed tip record and prove: the blob exists at the tip, the tip's only parent equals recorded `headSha` (the assembled package), identity-binding diff is only the record path, and `phase_ready_for_pr` inclusion evidence holds. Do not rewrite `headSha` to the embedding commit to silence that check. Unsealed records must not reuse forged extra sealed/merge/gate identity fields; `sealedSha` and candidate `sourceSha` bind to the identity-binding tip, while `namedGateEvidence.sha` stays on the assembled package. Isolated assembly has no deployment or promotion authority.

## Configuration

Repository config file (optional): `.github/linktrend-delivery-mode.json`

```json
{
  "schemaVersion": 1,
  "deliveryMode": "phase-integration",
  "phaseBranchPrefix": "phase/"
}
```

Environment override (tests / automation): `LINKTREND_DELIVERY_MODE=issue-pr|phase-integration`.

When unset, default is **`issue-pr`** so existing consumers keep current behavior.

`phaseBranchPrefix` is shared by Packager discovery (`is_allowed_work_branch`) and required branch-source CI policy (`scripts/gitops/work-branch-allowlist.sh` / `branch-source-policy.yml`). A custom prefix (for example `wave/`) must be allowlisted consistently in both places.

## Named gates (unchanged ids)

Gate ids remain `fast-gate`, `staging-gate`, and `release-gate`. Application-specific CI job names map to those ids via repository variables. Consumer-owned CI workflows are never overwritten by managed sync.

Exact-SHA fail-closed rules apply equally to Issue PRs and Phase PRs.

## Non-goals

- Not a live checkout/symlink dependency for consumers.
- Not mandatory Bugbot on checkpoints.
- Not GitHub Issues as an operational database.
- Not consumer rollout or live GitHub settings mutation by the packaging agent.
