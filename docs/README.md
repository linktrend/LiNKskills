# LiNKskills documentation

This directory is the home for repository documentation. Start with:

- `LINKSKILLS-INTENT.md` for scope and purpose.
- `LINKSKILLS-TECHNICAL-PRD.md` for the implemented architecture.
- `LINKSKILLS-OPERATIONS-MANUAL.md` for operations.
- `OPEN-ISSUES.md` for genuinely open work.
- `runbooks/` for current procedures.

Historical material belongs in `archive/` and is not implementation authority.
The root-level `archive/` directory is a self-contained retired code snapshot,
not an active documentation tree; it remains outside `docs/` so its historical
layout and recoverability are preserved. The root-level `evidence/` directory
is also intentional because certification code and migrations consume those
paths directly.

As of 2026-08-11, repository integration branches are synchronized, the VPS
Skills service is healthy, and OpenClaw/Lisa uses the native Skills bridge.
Future claims about an exact deployed LiNKskills commit still require a fresh
deployment receipt; service health alone is not source-version proof.
