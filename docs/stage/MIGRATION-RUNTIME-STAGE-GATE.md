# Migration / runtime stage gate — SKILLS-W20

**Lane:** B
**Date:** 2026-08-01
**Skills commit (workspace start):** `35d528f510cfb41bfab9ee306556dcd7a495ff16`
**Platform pin (read-only):** `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8`

## Verdict

| Gate | Status |
|---|---|
| Local manifest hash package | **READY** (hashes match; structural tests) |
| Local disposable Postgres migration/RLS proof | **READY** when ephemeral suite runs (Docker/DSN) — see evidence JSON |
| Stage shared DB apply | **BLOCKED** — no Platform stage apply receipt in this packet |
| Stage backup / restore dry-run | **BLOCKED** — template only; no filled receipt |
| Live apply by Skills | **FORBIDDEN** — Platform alone applies live |
| Sealed certifying executor (`network_isolation=denied`) | **BLOCKED** on macOS lane host — see certification readiness |

## Authority

- **LiNKplatform alone** applies live migrations to shared Supabase (stage/prod).
- LiNKskills authors SQL + hashed manifest + ephemeral proofs; does not hold stage/prod apply credentials for this lane.
- Platform repo is read-only for this packet (`/Users/linktrend/Projects/LiNKplatform` @ pin above).

## Inputs consumed

- `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md`
- `docs/migrations/REVIEW-QUEUE-000008-NOTE.md`
- `docs/migrations/REVIEW-QUEUE-000009-NOTE.md`
- `docs/migrations/PREFLIGHT-STAGE-READINESS.md`
- `docs/migrations/BACKUP-RECEIPT-TEMPLATE.md`
- `supabase/migrations/20260715_000002_*.sql` … `20260730_000009_*.sql`

## What “ready” means here

**Ready for Platform handoff** of an additive `lskills` package (hashes verified; local ephemeral optional proof recorded).
**Not ready** to claim stage schema applied, catalog live counts, or production DSN.

## Hard stop conditions

Proceeding to “stage migrations applied” language without:

1. Filled backup receipt (pre-apply + restore dry-run), and
2. Platform apply receipt citing matching SHA-256 rows, and
3. Post-apply verification SQL evidence

…is a process failure. Prefer open blockers over invented receipts.

## Related

- `docs/stage/CERTIFICATION-RUNTIME-READINESS.md`
- `evidence/stage-readiness/migration-preflight-local.json`
- `evidence/stage-readiness/sealed-linux-evaluation-gap.md`
