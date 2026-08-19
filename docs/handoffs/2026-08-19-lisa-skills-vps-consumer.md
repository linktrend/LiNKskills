# Lisa reusable skills: VPS consumer handoff

Date: 2026-08-19 (Asia/Taipei)
Owner: Codex Desktop Agent
Consumer: OpenClaw Prime Lisa on the VPS

## Outcome

Four reusable skills were added to LiNKskills. Lisa-specific schedules, private
data, credentials, permissions, and operational workflows remain in OpenClaw
Prime; they are not embedded in these provider skills.

Published skill IDs:

- `time-capacity-planner`
- `personal-compliance-tracker`
- `operational-reporting`
- `private-health-ledger`

## Source evidence

- Issue branch: `issue/128-add-lisa-time-management-compliance-reporting-an`
- Skill implementation commit: `303b7fa9e0e588b0553a1ba3ee1a3acf82cb1d2d`
- Catalog publication commit: `d65a950165069da51d186d8972acbebcd02b068b`
- Branch pushed to `origin`.

## Validation

- `python3 validator.py --repo-root . --scan-all` — passed; only pre-existing
  execution-ledger warnings remain.
- Per-skill validator runs for all four new IDs — passed.
- `python3 scripts/build-catalog-index.py --check` — passed (39 skills).
- `python3 -m pytest -q tests/skill_runtime/test_catalog_provenance.py tests/skill_runtime/test_skill_runtime.py` — 14 passed.

## VPS deployment evidence

- Active release: `/opt/linktrend/releases/LiNKskills/303b7fa9e0e588b0553a1ba3ee1a3acf82cb1d2d`
- `/opt/linktrend/LiNKskills` points to that release.
- `linkskills.service` is active.
- `GET http://127.0.0.1:18788/ready` returned `ready: true`, `catalog_loaded: true`,
  `skill_count: 39`, and `store_reachable: true`.
- The live catalog contains all four published IDs.
- The macOS archive had inserted 702 AppleDouble metadata files. Those generated
  `._*`/`.DS_Store` artifacts were removed from the deployed release only; no
  source skill files were removed. Future archives must use `COPYFILE_DISABLE=1`.

## Lisa consumer evidence

Lisa's production OpenClaw configuration has the LiNKskills HTTP connector
enabled with discovery and governed execution enabled and endpoint
`http://127.0.0.1:18788`.

Read-only Lisa agent run `6e1de427-d046-43ba-95ee-8448e1238cd1` searched the
live catalog through `skills_search` and returned `Found` for all four IDs.

## Remaining boundary

This proves source validation, VPS service readiness, catalog publication, and
Lisa-side discovery. It does not certify any skill as `usable`; all four remain
catalogued as `draft` until their independent LiNKskills certification/evidence
process is completed. It also does not change Lisa's calendars or private health
data.
