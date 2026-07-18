# Branching and Deployment Policy

Owner: LiNKtrend Platform  
Last updated: 2026-07-18

## Purpose

Protected promotion so production catalog checkouts are deterministic and auditable.

## Branch Model

- `development` — integration branch for agent / issue work (PRs land here).
- `staging` — pre-prod promotion target.
- `main` — production-only source for VPS / consumer pin SHAs.

Issue branches: `issue/<id>-<slug>`. Optional ad-hoc: `dev/<machine><ide>`.

## Promotion Flow

1. Develop on `issue/*` or `dev/*`.
2. Open PR → `development`; CI must pass.
3. Promote `development` → `staging` (Principal / release owner).
4. Promote `staging` → `main` (Principal / release owner).
5. Deploy consumer hosts / VPS checkouts only from a tagged commit on `main`.

## Required Gates

- CI must pass on `development`, `staging`, and `main` PRs.
- Catalog validator + eval-suite presence + catalog index freshness + unit tests.
- No revived Logic Engine deploy surface.

## Deployment Rules

- Production skill checkout source is `main` only.
- Optional staging VPS may track `staging`.
- Every production release should be tagged (example: `v2026.07.18-1`).
