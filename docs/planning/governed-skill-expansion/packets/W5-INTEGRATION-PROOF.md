# Wave 5 — Integration and Proof

## PKT-23 — Cross-source evaluation and qualification evidence

**Depends on:** PKT-05, PKT-22.

Run the complete source, security, licence, compatibility, functionality, privacy, and role-applicability evaluation matrix. Record each release as qualified, draft/eval-pending, quarantined, rejected, incompatible, deprecated, or superseded. A preserved collection may contain nonqualified members; the evidence must not imply collection-wide qualification.

**Acceptance:** Every intended selectable release has executed evidence; every nonselectable release has a reason; no real private data; exact release/source/evaluator identity and result digests are recorded.

## PKT-24 — Catalogue, migrations, supersession, and authoritative docs

**Depends on:** PKT-02, PKT-03, PKT-04, PKT-23.

This is the only content packet allowed to update shared generated catalogue files and principal product documentation. Generate the family hierarchy and catalogue; add explicit legacy/draft migration mappings; reconcile Intent, Technical PRD, Operations Manual, Open Issues, MCP/API and integration handoffs; package the final migration manifest. Do not apply migrations, configure consumers, publish releases, or deploy.

**Acceptance:** Catalogue generation is deterministic; all exact resources resolve; no duplicate authority remains; legacy transition/removal criteria are explicit; docs distinguish source from live proof; migration hashes/rollback/forward-fix are complete.

## PKT-25 — Exact-tree provider source verification

**Depends on:** PKT-24.

On the serially integrated exact Phase candidate, run focused packet checks, all relevant negative probes, repository-wide validation, catalogue check, isolated-package tests, secret/privacy scan, and exact-diff audit. Use the durable verification-liveness contract for long Full commands. Bind results to the physical checkout, commit, tree, commands, and evidence digests.

**Acceptance:** Exact source candidate passes; no merge-ref receipt is treated as promotable; all issue commits are ancestors; no owned-path leak or secret; unresolved external proof remains explicitly held.

## PKT-26 — Independent definition-of-done reconciliation

**Depends on:** PKT-25 plus XPKT-04 and XPKT-05 receipts supplied to the verifier.

An independent verifier classifies every PRD requirement as implemented/proven, implemented/not proven live, partial, omitted, different from plan, blocked by another repository, or excluded. It compares exact provider, Platform, Autowork, OpenClaw, stage/VPS, and production identities and rejects copied narrative as proof.

**Acceptance:** All mandatory definition-of-done items are proven at their claimed evidence level; no contract/ownership/privacy/activation contradiction remains; otherwise the package remains HOLD with exact correction packets.

## Integration rollback

- Source: revert the Phase integration commit or restore the prior exact qualified pointer.
- Migration: use the reviewed forward-fix/rollback plan under Platform ownership.
- Consumer: restore prior OpenClaw exact pins and disable the new provider path.
- Collection: retain immutable releases but remove selectability/current pointers.
- Production: follow owning repository rollback; never rewrite release artifacts.
