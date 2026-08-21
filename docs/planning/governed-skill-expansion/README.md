# LiNKskills Governed Skill Expansion — Execution Package

**Status:** Final planning package; implementation not authorized

**Authoritative installed baseline:** LiNKskills remote `main` commit `ded1baa63939db92f7616ac7393401a702d881de`, tree `d03e551d9c0189a3f22d67663a53cb68235f3c1d`

**Execution protocol:** Coding Execution Protocol `1.0.1`, amendment `V25_BOOTSTRAP_LEAN`, distributed by IDE Development `2.5.1`

This package adds the approved governed-skill expansion to the existing LiNKskills architecture. It does not replace or duplicate the Program Intent, Technical PRD, Operations Manual, accepted ADRs, or completed internal-launch work. Where the older internal-launch plan describes flat discovery, provider-side execution, or all-usable visibility without the three settled eligibility gates, this package is the later and narrower authority.

## Reading order

1. [`PRD.md`](./PRD.md) — final product requirements and definition of done.
2. [`FROZEN-INTERFACES.md`](./FROZEN-INTERFACES.md) — decisions executors must not reinterpret.
3. [`DEPENDENCY-GRAPH.md`](./DEPENDENCY-GRAPH.md) — waves, ready sets, cross-repository gates, and proof levels.
4. [`REQUIREMENTS-TRACEABILITY.md`](./REQUIREMENTS-TRACEABILITY.md) — requirement-to-packet and proof coverage.
5. [`LISA-CANARY-BINDINGS.md`](./LISA-CANARY-BINDINGS.md) — exact OpenClaw-owned instance acceptance values kept out of reusable releases.
6. [`EXECUTION-MANIFEST.json`](./EXECUTION-MANIFEST.json) — schema-valid LiNKskills packet manifest in `PLAN` state.
7. The assigned file under [`packets/`](./packets/) — bounded work and acceptance criteria.
8. [`cross-repository/HANDOFF-PACKETS.md`](./cross-repository/HANDOFF-PACKETS.md) — work owned by Platform, OpenClaw, LiNKautowork, or another repository.

## Authority and reconciliation

- [`../../LINKSKILLS-INTENT.md`](../../LINKSKILLS-INTENT.md) remains authoritative for Program purpose and exclusions.
- [`../../LINKSKILLS-TECHNICAL-PRD.md`](../../LINKSKILLS-TECHNICAL-PRD.md) remains the implemented-system reference.
- [`../../LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](../../LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md) remains historical execution authority for the internal-launch foundation already delivered.
- This package is authoritative only for the new provider-v2 completion, external-collection lifecycle, approved shared skills, four Lisa-originated families, nine business families, role manifests, and associated consumer conformance.
- Archived documents remain provenance, not implementation authority.

## Execution hold

Approval of these documents authorizes planning acceptance only. Execution requires a separately recorded founder approval bound to the manifest digest. Before the first mutation, the orchestrator must:

1. verify the IDE Development `2.5.1` consumer surfaces against authoritative remote `main` commit `ded1baa63939db92f7616ac7393401a702d881de` or an explicitly approved descendant containing the identical installed package;
2. record the then-current approved execution-base commit and tree in the manifest;
3. regenerate and validate the manifest if that identity differs from this planning baseline;
4. verify all packet path ownership against concurrent work;
5. create issue branches and acquire packet-repository leases; and
6. stop at every reserved protocol, migration, live-provider, publication, main-promotion, activation, or production-deployment gate until its exact approval is recorded.

The original planning checkout was stale. Authoritative remote `main` was read back at `ded1baa63939db92f7616ac7393401a702d881de`; `.ide-development/VERSION`, installed state, execution protocol, contracts, root `AGENTS.md`, and both Codex/Cursor entrypoints prove the LiNKskills v2.5.1 rollout. Re-reading those surfaces at execution start is exact-candidate verification, not an outstanding portfolio rollout.

## Package index

| Wave | Packet file | LiNKskills packets |
|---|---|---|
| 0 | `packets/W0-FOUNDATION.md` | PKT-00–PKT-04 |
| 1 | `packets/W1-SHARED-METHODS.md` | PKT-05–PKT-08 |
| 2 | `packets/W2-LISA-CANARY-SKILLS.md` | PKT-09–PKT-12 |
| 3 | `packets/W3-BUSINESS-FAMILIES-A.md` | PKT-13–PKT-17 |
| 4 | `packets/W4-BUSINESS-FAMILIES-B-ROLES.md` | PKT-18–PKT-23 |
| 5 | `packets/W5-INTEGRATION-PROOF.md` | PKT-24–PKT-26 |
| Cross-repository | `cross-repository/HANDOFF-PACKETS.md` | XPKT-01–XPKT-05 |

## Unresolved material decisions

No unresolved product decision prevents approval of this package. Three implementation-time selections remain deliberately bounded:

- the exact Google upstream commit is the latest candidate that passes review when PKT-05 starts;
- each external business-skill source is accepted, adapted, or rejected only after its packet records licence, integrity, security, maintenance, compatibility, and evaluation evidence; and
- live hosting, migration sequencing, OpenClaw file ownership, and polling cadence are selected by their owning repositories within the frozen interfaces.

None permits an executor to broaden scope, auto-activate a skill, or bypass a founder-reserved action.
