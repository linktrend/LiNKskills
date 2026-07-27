# OpenClaw Handoff — Skills MCP Contract Fragment

- **Status:** Contract / fake / conformance only
- **Date:** 2026-07-27
- **Fragment:** `configs/fragments/openclaw-skills.mcp.json.fragment`

## Ownership

| Asset | Owner |
|---|---|
| Skills MCP contract fragment + fake conformance in LiNKskills | **LiNKskills** |
| OpenClaw/Lisa managed MCP, plugins, hooks, buffers, profiles | **OpenClaw Prime** |

## Scope of this handoff

This repository supplies a **contract fragment** describing the Skills MCP operations, auth claim requirements, and local gateway wiring. It does **not** mutate OpenClaw.

Proven here:

- fake Platform claims verifier;
- gateway + MCP operation surface;
- no-secrets fragment shape.

Not proven / not performed here:

- live OpenClaw plugin install;
- OpenClaw profile or managed MCP edits;
- production credential wiring.

## Ask of OpenClaw owner

Consume the fragment as an integration contract. Wire host-side MCP only under OpenClaw ownership. Return any contract defects to LiNKskills; do not ask LiNKskills agents to edit OpenClaw.
