# Install, upgrade, and rollback (provider-v2 artifact)

This note is the Skills-owned install contract for the production
`skills.api.v0.2` Gateway/MCP artifact. It does not authorise live compose
edits, image publish, or Server 01 mutation (ED-06/ED-08 / Platform).

## Install (hash-locked source)

1. Install public-PyPI pins with `--require-hashes -r requirements-dev.lock`.
2. Install local packages in the ENV-00 order (`core` → `tool_runtime` →
   `gateway` → `gateway[postgres]` → `client` → `mcp_server` → …).
3. `packages/contracts` and `packages/persistence` stay on `PYTHONPATH`.
4. Production HTTP entrypoint: `linkskills-gateway` (serves `/v1` compatibility
   and `/v2` production on one process).
5. Production MCP entrypoint: `linkskills-mcp-v2` (protocol `2026-07-28`).
   Legacy `linkskills-mcp-server` remains the observed v0.1 adapter.

## Upgrade

- Keep the current v0.1 image digest for rollback before any live replace.
- Point new traffic at `/v2` and `linkskills-mcp-v2` only after ED-04
  selectability and consumer pins exist.
- Do not rewrite immutable releases.

## Rollback

Drain the candidate. Restore the retained v0.1 image
`sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f`
and release `7067716fef5189a1427a7cf9b0847cec898e19de` with the existing
compose projection. Platform owns live compose. Immutable catalogue rows stay.

## Removal gate for the v0.1 adapter

Remove `/v1` and legacy MCP tools only after every admitted consumer uses
v2, a rollback drill has succeeded, and no live v0.1 client remains.
