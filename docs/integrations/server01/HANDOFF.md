# Server 01 candidate handoff (ED-06 / issue 328)

- **Packet:** ED-06 — Build and prepare the Server 01 deployment candidate
- **Issue:** `#328` `issue/328-build-the-server-01-candidate`
- **Owner of this pack:** LiNKskills (source overlay, image definition, checks)
- **Live compose / secrets / containers:** Platform / Server 01 only
- **Status:** **CANDIDATE_NOT_DEPLOYED** — hosted image digest **HOLD**

This pack is the Platform-consumable Skills v2 candidate. It does not edit
`/srv/linktrend/deploy/compose/core-services.compose.yml`, publish an image,
render GSM secrets, or start containers.

## What to apply later (Platform)

1. Independently build `docs/integrations/server01/Dockerfile.candidate` as
   `linux/amd64`, non-root UID/GID `10002`, and record the image `sha256` digest
   plus SBOM. Reject any digest equal to the retained v0.1 image unless this is
   an explicit rollback.
2. Substitute only Platform-owned readbacks into
   `docs/integrations/server01/compose.overlay.yml`:
   - `REPLACE_WITH_HOSTED_LINUX_AMD64_DIGEST`
   - `REPLACE_WITH_PLATFORM_READBACK_NETWORK`
   - `REPLACE_WITH_PLATFORM_READBACK_STATE_VOLUME`
   - `REPLACE_WITH_PLATFORM_AUTHENTICATOR_MODULE`
3. Keep published ports loopback-only (`127.0.0.1:18798:8787`).
4. Retain the current v0.1 image
   `sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f`
   and release `7067716fef5189a1427a7cf9b0847cec898e19de` until ED-08 acceptance.
5. Treat container Docker health and `GET /health=200` as liveness only.
   Cutover requires `GET /ready=200` with store reachability after Platform
   receipts (ED-08).

## Entrypoints

| Surface | Command |
|---|---|
| HTTP production | `linkskills-gateway` serving `/v2` (legacy `/v1` remains until the removal gate) |
| MCP production | `linkskills-mcp-v2` |
| Legacy MCP | `linkskills-mcp-server` — retained, not the candidate default |

## Validation (Skills-owned, no live host)

```bash
python3 scripts/server01_candidate.py validate
python3 -m pytest -q tests/deploy/test_server01_candidate.py
```

## Rollback

See `docs/integrations/server01/ROLLBACK.md`. Drain the candidate, restore the
previous compose projection and image, and keep failed-candidate evidence.
Live apply remains ED-08.
