# Preflight — stage readiness (migrations / runtime)

**Packet:** SKILLS-W20-STAGE-READINESS
**Lane:** B (migrations / runtime gate)
**Authoring repo:** LiNKskills
**Live apply authority:** **LiNKplatform alone** applies live shared Supabase migrations. Skills agents must not apply to stage/prod.

## Purpose

Checklist before any stage claim that depends on `lskills` schema presence, RLS, gateway persistence, or review_queue. Local ephemeral proofs are **not** stage apply evidence.

## Manifest pin

| Item | Value |
|---|---|
| Manifest | `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md` |
| Ordered SQL | `000002` … `000009` (see manifest table) |
| Hash check (local) | All eight SHA-256 rows must match on-disk SQL bytes |
| Additive canary seed (000010) | `docs/migrations/MANIFEST-20260803-lskills-canary-echo-usable-seed.md` + `docs/migrations/CANARY-ECHO-000010-NOTE.md` — packages `canary-echo` usable state; **does not** clear B1–B5 |
| Platform pin (read-only consumer) | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` at LiNKplatform |

## Hard blockers (stage remains BLOCKED until cleared by Platform evidence)

| ID | Blocker | Cleared only by |
|---|---|---|
| B1 | No Platform-owned **stage DB apply receipt** for this Skills SQL package | Filled apply receipt citing manifest hashes + verification SQL |
| B2 | No filled **backup receipt** (pre-apply + restore dry-run) | `docs/migrations/BACKUP-RECEIPT-TEMPLATE.md` completed by Platform |
| B3 | Stage DB apply evidence **absent** or invented | Real Platform evidence path/ref — never Skills-fabricated |
| B4 | Platform foundation (`platform.organizations`, role helpers) not proven on stage | Platform foundation apply/verify evidence |
| B5 | Skills agent or non-Platform operator applied / plans to apply live | Stop; reaffirm Platform-only apply |
| B6 | Sealed Linux `network_isolation=denied` certification unavailable on this host | Certifiable Linux/`bwrap` host (see sealed-linux gap doc) — separate from migration apply |

If **any** of B1–B5 is open, stage migration/runtime gate = **blocked**. B6 blocks certification/usable promotion, not the SQL hash package itself.

## Soft / local proofs (do not clear B1–B5)

| Check | Local status expectation |
|---|---|
| Manifest SHA-256 vs SQL bytes | Must pass in `tests/migrations/` |
| Ephemeral disposable Postgres apply + RLS | May pass when Docker/`LINKSKILLS_TEST_PG_DSN` available |
| Structural SQL invariants (additive, no drop schema) | Must pass without DB |

## Preflight steps (Skills-owned, read-only against live)

1. Confirm branch ancestor and Skills pin for the packet.
2. Recompute SHA-256 for every manifest SQL path; fail closed on mismatch.
3. Confirm review-queue notes: ordered apply `000007` → `000008` → `000009`; Platform-only live apply.
4. Run `tests/migrations/` (structural + optional ephemeral). Record results under `evidence/stage-readiness/`.
5. Demand Platform backup receipt + apply receipt before any “stage schema ready” language.
6. Refuse to invent stage endpoints, dump IDs, or apply timestamps.

## Explicit apply rule

> **LiNKplatform alone applies live.** LiNKskills hands this manifest + SQL to the platform migration owner. Skills agents must not apply to stage/prod.

Local disposable/ephemeral Postgres only for Skills proofs.
