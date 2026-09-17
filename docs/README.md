# LiNKskills documentation

This directory is the home for repository documentation. Start with:

- `LINKSKILLS-INTENT.md` for scope and purpose.
- `LINKSKILLS-TECHNICAL-PRD.md` for the implemented architecture.
- `LINKSKILLS-OPERATIONS-MANUAL.md` for operations.
- `OPEN-ISSUES.md` for genuinely open work.
- `end-to-end-delivery/README.md` for the Server 01 operational-delivery plan,
  initial five-release scope, current live evidence, execution manifest, and
  acceptance gates.
- `planning/governed-skill-expansion/` for the final IDE v2.5.1 PRD,
  dependency graph, manifest, and approval-gated execution packets for provider
  v2 completion, governed external collections, approved reusable skills, and
  role manifests.
- `runbooks/` for current procedures.

Historical material belongs in `archive/` and is not implementation authority.
The root-level `archive/` directory is a self-contained retired code snapshot,
not an active documentation tree; it remains outside `docs/` so its historical
layout and recoverability are preserved. The root-level `evidence/` directory
is also intentional because certification code and migrations consume those
paths directly.

The historical 2026-08-11 service-health and OpenClaw/Lisa evidence does not
prove current readiness or end-to-end use. The 2026-09-10 Server 01 inspection
recorded in `end-to-end-delivery/STARTING-POSITION.md` confirms an exact running
release and process health, but `/ready` fails because the production store is
unreachable and current provider/selectability/consumer acceptance remains
unproven.
