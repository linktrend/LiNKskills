# Evidence-based starting position

**Inspection date:** 2026-09-10 (Asia/Taipei)

The classifications below separate source, installed configuration, and
demonstrated live behavior. Historical receipts are retained but do not prove
the current runtime unless explicitly re-read from the accepted identity.

## Verified working now

| Surface | Evidence | Limit of proof |
|---|---|---|
| Current protected source identity | LiNKskills `development` is `7a813f5…`; `main` is `7067716…`; both resolve to tree `d0bb392…`. | Does not prove live behavior or acceptance. |
| Existing production release and image | Server release manifest binds `main` `7067716…` / tree `d0bb392…`; container image is `linktrend/linkskills@sha256:7cf2780…`. | Image/source identity and running installation only. |
| Hardened container baseline | `linktrend-linkskills` runs as UID/GID `10002`, read-only root, all capabilities dropped, no-new-privileges, bounded CPU/memory/PIDs, read-only secret mount, separate runtime-state mount, restart `unless-stopped`. | Configuration readback; not service readiness. |
| Process liveness and metrics | Loopback `127.0.0.1:18798/health` returned 200; metrics returned request/readiness counters; Docker health is healthy. | `/ready` fails, so not operational readiness. |
| Authentication fail-closed edge | Unauthenticated `POST /v1/skills_list` returned 401 `auth_missing`; production auth env is present. | Does not prove a valid Platform token succeeds. |
| Catalogue source loaded | Live `/ready` reports 59 loaded skills; deployed `catalog/index.json` has 59 entries. | All 59 source entries are `draft`; no selectability proof. |
| Server shared network | Container shares the existing private core-services Docker network with OpenClaw/Lisa, Brain, and related services. | Network adjacency is not consumer integration. |
| Local initial-seed artifacts | Six immutable adapter bundles and 207-member classification exist; 182 are approved only for internal canary classification. | Receipt explicitly says no live provider publication, pointer change, stable qualification, ordinary selectability, or consumer activation. |

## Existing but requiring testing, configuration, or repair

| Surface | Current evidence | Required closure |
|---|---|---|
| Production readiness | `/ready` returns 503: auth configured and catalogue loaded, but Postgres store probe reports `OperationalError` and `store_reachable=false`. | Platform database/migration/credential recovery, DSN/role readback, store probe 200, and failure-path proof. |
| Gateway contract | Running container exposes legacy `skills.api.v0.1`; repository contains provider-v2 `skills.api.v0.2` source. | Choose/build/deploy the v2 entrypoint and prove standard resource-first MCP/HTTP conformance; retain legacy only under an explicit compatibility gate. |
| Platform auth | PACI issuer/JWKS/introspection variables and private key mount exist; invalid/no token fails closed. | Valid intended identity, wrong-scope/audience, expiry, rotation, revocation, introspection, and mint allowlist canaries. |
| Initial qualified locks | Installed IDE lock names five LiNKskills releases as qualified, but is pinned to historical provider `e3d80fd…`; dual-app proof is `HOLD`. | Re-evaluate at current source, live-publish exact releases, update pins only after qualification, and prove Cursor/Codex. |
| Lisa connection | Recovery status says Lisa retains existing identity-backed Brain MCP and Skills HTTP bindings; all five agents discover Skills-use tools. | No identity-backed read was invoked; Lisa end-to-end functional acceptance is unproven. |
| Observability | Prometheus/Grafana/node exporter are healthy at server level and Gateway metrics are emitted. | Confirm Skills target, dashboards, redaction, alert routing, store/auth/latency/SLO coverage, and actionable alert test. |
| Backup/recovery | Server retains releases, image, runtime state, and operational backup machinery. | Skills registry/evidence/config backup scope, isolated restore, restart, drain, pointer rollback, prior-image rollback, and acceptance receipts. |
| Librarian | Skills domain package and Platform generic runner source exist. | Versioned production worker load, identity/least privilege, queue/retry/DLQ, supervised pass, schedule, disable, and no prompt-only certification. |

## Missing

- Current live production publication and selectability evidence for the five
  initial releases.
- Current executed-case qualification receipts bound to the production profiles
  and live immutable release digests.
- Current Cursor, Codex, and Lisa end-to-end receipts at one accepted provider
  identity.
- A production-ready provider-v2 route and exact consumer connection contract.
- Skills-specific live backup/restore and rollback acceptance.
- Complete founder-facing live status that separates source, qualification,
  selectability, consumer, server, and production evidence.

## Unknown until approved execution

- Which exact Platform database defect/credential/migration step causes the
  current Skills `OperationalError`; no secret-bearing DSN was printed or tested
  in this planning task.
- Whether all required `lskills` migrations are present in current stage and
  production, and whether their fingerprints match the current package.
- Whether the existing image actually exposes provider-v2 through its configured
  entrypoint or only contains the source code.
- Exact consumer-side current pins and safe tool permissions outside this
  repository, except for the preserved HOLD/disabled records reviewed here.
- Current backup coverage for runtime state and database domain objects.
- Final private endpoint/route selected by Platform. The existing Tailscale
  routes do not expose port `18798` directly.

## Upstream dependency status

Platform is an active, specific dependency, not a blanket planning blocker.
The recovery task reports both stage and production projects healthy at the
provider level and has integrated/staged PostgreSQL 17 backup support, but its
2026-09-10 status remains HOLD for the scoped database window, governed backup,
isolated restore, migrations `000018`–`000022`, native `svc_platform`, identity
registration, runtime activation, and acceptance. LiNKskills can execute all
source, qualification-fixture, artifact, consumer-contract, and deployment
preparation packets independently; live database, identity, and production
acceptance gates wait for exact Platform receipts.
