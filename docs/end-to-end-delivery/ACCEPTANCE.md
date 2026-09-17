# ED-10 final-acceptance framework

**Packet:** `ED-10` (ISS-10 / GitHub issue `#354`)
**State:** `FRAMEWORK_ONLY` / `HOLD`
**Final acceptance declared:** **no**

This document is the fail-closed ledger for the later ED-10 decision. It
defines required receipts, identity compatibility, and the rule that **pending
is not passed**. It does not accept the delivery, modify production or consumer
configuration, or invent runtime evidence.

Owned paths for this packet are only:

- `docs/end-to-end-delivery/ACCEPTANCE.md`
- `evidence/end-to-end-delivery/ed-10/`

## 1. What this checkpoint is and is not

This checkpoint **prepares** the acceptance framework. It is not
`FUNCTIONAL_ACCEPTED`, `INTERNAL_LAUNCH_COMPLETE`, or production acceptance.

| Claim | This checkpoint |
|---|---|
| Framework and criteria exist | yes |
| Required receipt slots named | yes |
| Compatible real ED-08 / ED-09 / IMP-00 / OSS proof consumed | **no** — those files are absent on this admitted identity |
| Any Definition of Done row marked `PASS` | **no** |
| Aggregate “percent complete” used as a substitute | forbidden |
| Nested workers, PRs, merge, deploy, or live mutation | forbidden |

Machine-readable companions:

- [`evidence/end-to-end-delivery/ed-10/final-acceptance.json`](../../evidence/end-to-end-delivery/ed-10/final-acceptance.json)
- [`evidence/end-to-end-delivery/ed-10/receipt-compatibility.json`](../../evidence/end-to-end-delivery/ed-10/receipt-compatibility.json)
- [`evidence/end-to-end-delivery/ed-10/criteria-ledger.json`](../../evidence/end-to-end-delivery/ed-10/criteria-ledger.json)
- [`evidence/end-to-end-delivery/ed-10/oss-proof-slots.json`](../../evidence/end-to-end-delivery/ed-10/oss-proof-slots.json)

## 2. Decision rule

1. Every mandatory criterion starts as `PENDING` until an exact, compatible,
   real receipt is independently inspectable.
2. A criterion becomes `PASS` only when every required sub-proof is present,
   identities match, and no named blocker remains.
3. Missing, template, narrative-only, identity-mismatched, or fabricated
   evidence keeps the row `PENDING` or `HOLD`. It is never inferred to `PASS`.
4. The packet decision is `PASS` only if **all** mandatory rows are `PASS`.
   Otherwise the decision stays `HOLD`.
5. No row may be marked `PASS` in this framework until the required receipts
   exist at the paths below on a later admitted candidate.

`PENDING` means the work has not been proven. It is not a failure of a live
probe, and it is not a pass.

## 3. Required receipts (real, not placeholders)

ED-10 may consume only owner-supplied receipts. Absence on this checkout is
recorded as `PENDING` / `NOT_SUPPLIED`.

| Slot | Required path | What “real” means |
|---|---|---|
| ED-08 live deploy | `evidence/end-to-end-delivery/ed-08/deployment-receipt.json` | Observed Server 01 deploy/readback (`/health`, `/ready`, image digest, source commit/tree, backup, restart, rollback rehearsal). Not a planning template. |
| ED-09 canaries | `evidence/end-to-end-delivery/ed-09/final-acceptance.json` plus the named actor canary receipts that file binds | Ordered Cursor → Codex → Lisa representative use, negatives, and the 48-hour Cursor observation when claiming internal-launch completeness. |
| IMP-00 loop | `evidence/end-to-end-delivery/imp-00/improvement-loop-receipt.json` | **Accepted** improvement-loop receipt: historical PACI correction `6a2101d132b42010162595a2bab2c72fee6282da` is an ancestor of the candidate; `ResolveClaimsVerifierPaciIssuerPolicyTests` replayed; Librarian disposition recorded; bound to the ED-08 image/release and the accepted ED-09 canary. |
| OSS proof | slots in `oss-proof-slots.json` | Continuity, provenance, reproducibility, and rollback each have exact refs/digests. Planning inventory text is not that proof. |

Conditional L-FIX packets (`FIXGS-00` … `FIXTA-00`) are **not** ED-10
prerequisites. Unselected packets remaining `PLAN` must not be counted as
completed work.

## 4. Compatible identities

Receipts are usable together only when they describe the **same** accepted
candidate. Compatibility is conjunctive:

1. Same GitHub repository `linktrend/LiNKskills`.
2. Same protected or deployed source `commit` and `tree` (or an explicit,
   independently reviewed successor that lists the prior identity as ancestor).
3. Same provider image digest and release/channel pointer as ED-08.
4. ED-09 canaries were executed against that ED-08 provider identity, not a
   different checkout, image, pin set, or “latest”.
5. IMP-00 binds that same image/release **and** the accepted ED-09 canary
   identity; a loop receipt that only restates the historical Mac Mini commit
   is not sufficient.
6. OSS continuity/provenance/reproducibility/rollback proofs name the same
   image/release/source identity and a recoverable prior pointer.

If any field is missing, disagrees, or is only narrative, the set is
**incompatible**. ED-10 stays `HOLD`.

## 5. Criteria ledger (PRD §8)

Authoritative product text: [`PRD.md`](./PRD.md) §8. Status values in this
framework are only `PENDING` or (later) `PASS` / `HOLD`. None are `PASS` here.

| ID | Criterion | Required proof | Status now |
|---|---|---|---|
| DOD-01 | Exact protected source and deployed image/release, independently verified | Compatible ED-08 receipt + independent review | `PENDING` |
| DOD-02 | Production Gateway `/health=200` and `/ready=200`; auth and durable store reachable | Real ED-08 live readback | `PENDING` |
| DOD-03 | Provider-v2 discovery/retrieval and digest checks; no legacy execute on v2 | ED-08 provider probes | `PENDING` |
| DOD-04 | Five initial releases live-published, qualified, selectable only via intended pins | ED-03/ED-04/ED-05 identities bound into ED-08/ED-09 | `PENDING` |
| DOD-05 | Ordered Cursor, Codex, Lisa use; 48-hour Cursor observation for internal-launch | Compatible real ED-09 receipts | `PENDING` |
| DOD-06 | Fail-closed negatives (identity/scope, tamper, outage, disabled consumer) | ED-09 negative matrix at the ED-08 identity | `PENDING` |
| DOD-07 | Metrics, logs, alerts, founder report, Librarian, backup, restore, restart, drain, rollback | ED-07/ED-08/OSS rollback at compatible identity | `PENDING` |
| DOD-08 | Brain/Skills separation, privacy/redaction, least privilege, consumer tool authority | Cross-surface receipts; no payload leakage | `PENDING` |
| DOD-09 | Real failure/correction loop + tool blast-radius/rollback | **Accepted** IMP-00 receipt at compatible identities | `PENDING` |
| DOD-10 | Measured cost (database, request, model, storage, eval) and security/privacy/supply-chain with no launch blocker | Cost + assurance attachments bound to the same identity | `PENDING` |
| DOD-11 | All 59 catalogue entries classified; only the five initial releases selectable | Classification inventory bound to the candidate | `PENDING` |
| DOD-12 | Independent narrow reviews and final cross-surface reconciliation | Independent review of the exact candidate SHA | `PENDING` |
| DOD-13 | Later expansion remains disabled except separately approved material scope | ED-05 disabled expansion + ED-09 non-activation | `PENDING` |

Functional usability (`FUNCTIONAL_ACCEPTED`) may later be reported from ED-09
when the three actor flows pass at compatible identities. Strict
`INTERNAL_LAUNCH_COMPLETE` stays `HOLD` until the 48-hour Cursor observation
also passes. This framework does not assert either.

## 6. OSS continuity, provenance, reproducibility, rollback

ED-10 cannot pass on catalogue narrative or `OSS-INVENTORY.md` planning text
alone. Each OSS slot must later be filled with exact proof:

| Slot | Meaning | Status now |
|---|---|---|
| Continuity | The accepted candidate is a recoverable successor of the deployed/rollback identity; no silent “latest” substitution | `PENDING` |
| Provenance | Source commit/tree, image digest, lockfile/hash-locked install, and SBOM/supply-chain refs are named and inspectable | `PENDING` |
| Reproducibility | Hash-locked `requirements-dev.lock` / attested interpreter and the ED-06/ED-08 image can be re-identified; no unpinned compiler used as a substitute | `PENDING` |
| Rollback | Prior image/compose/pointers remain recoverable; rehearsal or equivalent receipt exists at the ED-08 identity | `PENDING` |

## 7. Prohibited actions for this packet

- Declaring final acceptance in prose or JSON.
- Editing product source, Skills, migrations, consumer activation, or deploy
  files.
- Fabricating ED-08, ED-09, IMP-00, or live Server 01 evidence.
- Opening a PR, self-review, self-merge, promotion, deployment, or nested
  workers.

When the required receipts exist on a later candidate, a distinct ED-10
decision run may populate `PASS` rows. That run is not this checkpoint.
