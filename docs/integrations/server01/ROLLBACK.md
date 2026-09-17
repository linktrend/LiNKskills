# Server 01 candidate rollback (source pack)

Live rollback is owned by Platform / Server 01. This file names the exact
previous state that must remain available until a later deploy packet is
accepted.

## Retained previous state

| Field | Value |
|---|---|
| Service | `linktrend-linkskills` |
| Image | `linktrend/linkskills@sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f` |
| Release commit | `7067716fef5189a1427a7cf9b0847cec898e19de` |
| Release tree | `d0bb392351994810173f730c47b63112c31e391b` |
| Contract | `skills.api.v0.1` |
| Live compose | `/srv/linktrend/deploy/compose/core-services.compose.yml` |
| Compose sha256 at ED-00 readback | `a114290bf485c51a9ffd297ede317e79a2ac708d088a90487b1c9eeae037cd67` |
| Publish | `127.0.0.1:18798` → container `8787` |

## Skills-side recovery

- Revert this issue checkpoint if the candidate overlay is rejected before
  deploy.
- Do not rewrite immutable catalogue rows or the retained v0.1 image.
- Do not rotate Platform credentials from LiNKskills.

## Platform-side recovery (not executed here)

1. `POST /drain` and wait for in-flight work (bounded 30s).
2. Restore the retained image digest and prior compose projection.
3. Confirm `/health` liveness and honest `/ready` (do not mask store failure).
4. Keep the failed candidate image/overlay for evidence.
