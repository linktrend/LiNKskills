# OSS continuity evidence framework

This document is the reusable record format and validation-ready checklist
for LiNKskills remaining end-to-end delivery. It does not replace
[OSS-INVENTORY.md](./OSS-INVENTORY.md), packet ownership in
[WORK-PACKETS.md](./WORK-PACKETS.md), or completed packet evidence under
`evidence/end-to-end-delivery/{ed-00,ed-01,ed-04,ed-05,ed-07,env-00,xp-00}/`.

**Status:** `FRAMEWORK_READY / NO_INSTALLATION_CLAIMED`

**Admitted starting identity (authoritative for this checkpoint's facts):**

| Field | Value |
|---|---|
| Repository | `linktrend/LiNKskills` |
| Ref | `issue/352-prepare-oss-continuity-evidence-and-validation-f` |
| Commit | `f97951feec6546ff924c65611802afd7ab19d2a3` |
| Tree | `9bd1ba9eb32885146317f25a1cd3b223d1540d9e` |

Refresh those four fields before any later packet uses a filled record.
A changed commit or tree invalidates prior filled identities. This
framework does not claim any runtime, image, consumer, or Platform
installation complete.

## Purpose

Remaining packets still need a single way to prove that an upstream or
shared artifact is:

1. **Preserved** as source or artifact (read-only by default).
2. Bound to an **immutable** version, commit, tree, and/or digest.
3. Accompanied by **provenance and licence** (or an explicit pending gap).
4. Installable only through a **reproducible**, hash-locked or digest-pinned
   procedure — never an unbounded resolver as the accepted path.
5. **Compatible** with the admitted compiler, CI matrix, and consumer
   profile, with unknowns left pending.
6. Subject to **explicit update review** before any pointer moves.
7. Reversible through a named **rollback** to a prior immutable identity.

Filled instances live under
`evidence/end-to-end-delivery/oss-continuity/`. Completed packet receipts
elsewhere must not be rewritten to satisfy this framework.

## Preservation policy (default)

Upstream, vendor, collection, archival, and Platform-owned surfaces are
**read-only by default**. LiNKskills may:

- copy interface facts and licence/notice paths already in this repository;
- record digests, commits, trees, and review outcomes;
- produce a new immutable identity after an approved update review.

LiNKskills may not, under this framework:

- overwrite vendor or upstream bytes in place;
- auto-promote a newer upstream because it is newer;
- treat catalogue presence, a green test, or a running container as
  installation or production acceptance;
- mutate live compose, GSM values, consumer repos, or protected branches.

Later catalogue expansion (54 other source-catalogue skills, six collection
adapters, 207 collection members) remains preserved and nonselectable.
See package [README.md](./README.md) and
[docs/INITIAL-SKILL-SEED-ROUTING.md](../INITIAL-SKILL-SEED-ROUTING.md).

## Record format

Each component uses one JSON object of kind
`linkskills-oss-continuity-record` (schemaVersion `1`). Required sections:

| Section | What it must bind | Fail-closed rule |
|---|---|---|
| `sourceArtifact` | Path, URI, or host surface; preservation mode | Missing location is `PENDING`, not invented |
| `immutableIdentity` | Version and/or commit and/or tree and/or digest | Truncated inventory strings stay truncated; do not pad |
| `provenanceLicense` | Declared licence, notice path, attribution duty | Conflict or absence is `PENDING` / `HOLD` |
| `reproducibleInstallation` | Exact command, lock/digest pin, owner | Never claim complete unless a named packet receipt exists |
| `compatibility` | Interpreter, OS/arch, CI, profile, requires-python | Missing local CI interpreter is diagnosed, not silently substituted as authority |
| `updateReview` | Who reviews; auto-promote forbidden | Poll/candidate files are non-promoting |
| `rollback` | Prior identity and restoring owner | No prior identity → rollback `PENDING` |

Allowed section statuses: `RECORDED_SOURCE_FACT`, `PENDING`, `HOLD`,
`NOT_APPLICABLE`. `PASS` is reserved for a later packet that cites this
record plus its own execution receipt. This framework never writes `PASS`
for installation.

Machine copies:

- schema: `evidence/end-to-end-delivery/oss-continuity/record.schema.json`
- policy: `evidence/end-to-end-delivery/oss-continuity/preservation-policy.json`
- filled registry: `evidence/end-to-end-delivery/oss-continuity/registry.json`
- reusable checklist: `evidence/end-to-end-delivery/oss-continuity/validation-checklist.json`
- worker toolchain note: `evidence/end-to-end-delivery/oss-continuity/toolchain-attestation.json`

Validate JSON with `python3 -m json.tool <file>`. Optional later check:
`jsonschema` against `record.schema.json` (dev lock pin `jsonschema==4.26.0`).

## Validation-ready checklist

Copy this table into a remaining packet's proof. Every row must be
`RECORDED_SOURCE_FACT`, `PENDING`, `HOLD`, or `NOT_APPLICABLE`. Unknowns
stay pending.

| ID | Check | Source of truth on this tree | Remaining-packet use |
|---|---|---|---|
| C-01 | Preserved upstream source/artifact located; preservation mode `read_only_default` unless a named LiNKskills-owned path is being newly published | OSS inventory; collection `LICENSE.upstream`; vendor paths | Do not edit vendor/collection bytes while filling the record |
| C-02 | Immutable version **and** commit **and/or** tree **and/or** digest recorded, or truncation/`PENDING` explicit | Protected refs in ED-00; ENV-00 lock; ED-04 release digests; inventory truncated image/source strings | Refresh before dispatch; changed identity invalidates the candidate |
| C-03 | Provenance/licence path recorded; attribution retained; licence conflicts called out | `pyproject.toml` `license = Proprietary` for umbrella; collection licence files; Google Workspace Apache-2.0 note | Do not invent SPDX when files disagree |
| C-04 | Reproducible install path is hash-locked or digest-pinned; unbounded `requirements-dev.txt` is compile input only | `docs/development/CLOUD-EXECUTION.md`; CI `pip install --require-hashes -r requirements-dev.lock` | Do not claim Server 01 / consumer / Platform install complete |
| C-05 | Compatibility vs `requires-python = ">=3.11"`, CI `ubuntu-24.04-arm` / Python 3.11, ENV-00 worker CPython 3.12.3 x86_64 | `pyproject.toml`; `.github/workflows/ci.yml`; `CLOUD-EXECUTION.md` | If Python 3.11 is absent on the worker, diagnose; CI remains compatibility authority |
| C-06 | Update requires explicit review; no automatic pointer/activation | Frozen interfaces §5; `collections/google-workspace` `update-candidate.json` non-promoting; XP-05 does not install product | Candidate ≠ current pointer |
| C-07 | Rollback names prior immutable identity and restoring owner | Packet recovery sections; ED-06/ED-08 prior image/compose; publisher pointer rollback | If prior identity is truncated or live-unproven, status is `PENDING` |

## Remaining delivery mapping

Packets that already have evidence directories on this tree (`ED-00`,
`ED-01`, `ENV-00`, `ED-04`, `ED-05`, `ED-07`, `XP-00`) keep those files
unchanged. This framework is for **remaining** work and for reuse when
those packets later produce a new identity.

| Remaining packet | Continuity obligation | Must not do under this framework |
|---|---|---|
| `ED-02` | Bind provider-v2 artifact identity; retain v0.1 image/compose as rollback target | Edit completed ED-00/ED-04 evidence; claim live v2 exposure |
| `ED-03` | Bind skill/eval/tool/runtime digests; executed-case evidence only | Rewrite ED-04 `eval_pending` rows in place |
| `ED-06` | Digest-pinned linux/amd64 image, SBOM/provenance, previous-state rollback pack | Edit live compose or `deploy/production/` |
| `ED-08` | Record deployed digest vs candidate; rehearsal rollback | Perform live deploy from this documentation packet |
| `ED-09` | Consumer pins stay disabled until owner apply; rollback is disable-then-ED-08 | Activate consumers or edit external repos |
| `IMP-00` / `ED-10` | Historical correction provenance; tool-pointer rollback | Fabricate a new defect; count unselected FIX packets as done |
| `FIX*` (conditional) | New immutable skill version; revoke/roll pointer; never rewrite the old release | Activate without an actual ED-09 failure |
| External XP-01–04 | Platform/consumer owners remain sole writers of live state | Repair Platform or shared consumer config from LiNKskills |

## Existing repository facts (do not treat as live completion)

Facts below are copied from this admitted tree only.

### Shared runtime inventory (from `OSS-INVENTORY.md`)

Reuse; do not install a second stack. Versions and full digests must be
refreshed at execution time. Inventory truncations are preserved:

- Docker Engine + Compose on LiNKserver 01, existing `linktrend-core-services`.
- LiNKskills Python image: running `linux/amd64` digest recorded as
  `sha256:7cf2780…`; source release `7067716…`. Full digest **pending refresh**.
- PostgreSQL/Supabase: existing Platform projects; Skills store probe fails
  (`OperationalError` in starting position). Live DDL is Platform-only.
- GSM, PACI (`audience` `lskills-api`, scope `lskills`), Tailscale (no
  direct Skills `18798` public ingress by default), Prometheus/Grafana/node
  exporter: reuse; Skills scrape/alerts unproven.
- Sealed Linux evaluator + Bubblewrap: digest-pinned image contract exists
  in repo; five-release executed qualification is remaining (`ED-03`).
- LiNKskills MCP: source package exists; target v2 is sessionless /
  resource-first; no separate public MCP daemon unless an approved adapter
  needs it (`ED-02` remaining).
- Generic Librarian host: Platform-owned; Skills domain worker source
  exists (`ED-07` source evidence present; production worker operation
  unproven).

Not required: Kubernetes, second staging VPS, Traefik, Redis, NATS, n8n,
second gateway/database/monitoring stack, retired Logic Engine.

### Source and lock pins

- ENV-00 hash lock: `requirements-dev.lock` SHA-256
  `cb534f8847e80e8af1fa115745f62650ee67488dde1a876da4f443361bf448c1`
  generated from `requirements-dev.txt` SHA-256
  `b0b0424f212cd0b468642888677c1527361eb3f81f12d674b6c3c343e6c7f0b0`.
  CI installs with `--require-hashes`. This is the public-PyPI **dev/test**
  pin, not a production image pin.
- Umbrella package `linkskills` `0.1.0`, `requires-python = ">=3.11"`,
  licence text `Proprietary`. No root `LICENSE` file on this tree.
- Planning baseline (ED-00, may be stale vs this branch tip):
  `development` `7a813f529f7b25a40fd3e88f74fb0e86c7c728d5` /
  tree `d0bb392351994810173f730c47b63112c31e391b`;
  `main` / deployed release `7067716fef5189a1427a7cf9b0847cec898e19de`
  / same tree `d0bb392351994810173f730c47b63112c31e391b`.
- Initial provider set (not claimed selectable in production):
  `git-safeguard@1.1.0`, `persistent-qa@1.0.0`,
  `repository-manager@1.0.0`, `skill-template@1.2.0`,
  `tool-architect@1.0.0`. ED-04 source receipt keeps
  `qualificationLifecycle` `eval_pending` and `liveProviderMutation` false.
- Local bootstrap adapters `agentsetup@1.3.0` and `agentcomply@1.3.0`
  are not provider catalogue skills.

### Vendor / collection preservation (later expansion; read-only)

| Surface | Recorded licence / pin on this tree | Full SHA-256 of licence/notice file |
|---|---|---|
| `collections/awesome-design/LICENSE.upstream` | MIT | `56e2dc0100744b958d87e5fc790f4e5ed2b5f483d6f2cbade4b6f7a0f5a03862` |
| `collections/emil-design/LICENSE.upstream` | MIT | `4ff5bdb7887ec1435c9cab0e8d1a7caee704d894d65c2a008ccc68b1cc2f260b` |
| `collections/taste-design/LICENSE.upstream` | MIT | `4575a543ab88dad12ccea7d97e563d0bce5b448b06072e65d3264497dad326df` |
| `collections/hybrid-development/LICENSE.gstack.upstream` | MIT | `e56fbb5b3d95756f3fa1cfefa24732ec79f18ece1ad08a4e79e00df57e8b198c` |
| `collections/hybrid-development/LICENSE.matt-pocock.upstream` | MIT | `0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5` |
| `collections/impeccable/LICENSE.upstream` | Apache License 2.0 text | `02bb8c3b4e70190e3986c0404ad2fd8d639b4f534252d82379cc1b502b6d1812` |
| `collections/impeccable/NOTICE.upstream.md` | Distilled platform refs; **original work MIT** (ehmo/platform-design-skills) | `c60a093c2845fd9fb82f9c6f742ece31f379f8190b535309d32d66c45ccffdcb` |
| Google Workspace collection README | Apache-2.0; reviewed `main` `a3768d0e82ad83cca2da97724e46bea4ff0e6dbd` / tree `28127e4c0edff4bdf9226369e7a2ef744b353c25`; historical `v0.18.1` `e9970db26fb32ca97f11ce0d8c7c53e4eedd81cc` | Path `collections/google-workspace/README.md`; vendor bytes under `vendor-skills/google-workspace/` |
| `tools/gws/vendor/link-gws-cli/LICENSE` | Apache-2.0 | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |

**Licence pending:** Impeccable collection stores Apache-2.0 licence text in
`LICENSE.upstream` while `NOTICE.upstream.md` attributes a subset of
reference files to an MIT original. Do not collapse these into one SPDX
expression in this framework.

Google Workspace `update-candidate.json` is a pending non-promoting
proposal and must not change a current pointer.

## Compiler and lock diagnosis (this worker, not a lock change)

Protected CI remains `ubuntu-24.04-arm` with Python **3.11** and
`python -m pip install --require-hashes -r requirements-dev.lock`.

ENV-00 attests a valid cloud worker of Ubuntu 24.04.4 LTS, Linux x86_64,
CPython **3.12.3**, because packages declare `requires-python = ">=3.11"`.
Python 3.11 is not present on this VM (`/usr/bin/python3` → 3.12.3). That
is a **known ENV-00 gap**, not permission to unpin or rewrite
`requirements-dev.lock`. Node 22.14.0 may be present; ENV-00 does not
require Node. There is no Node package manifest at repository root.

`packages/contracts` and `packages/persistence` have no `pyproject.toml`
and must not be added to the lock.

## How a remaining packet fills a record

1. Copy `record.schema.json` constraints; do not weaken sections.
2. Set `boundIdentity` to the packet's exact repository/ref/commit/tree.
3. Fill only facts readable from this repo, an already-committed receipt,
   or a named owner handoff. Leave the rest `PENDING`.
4. Keep `installationComplete: false` until that packet's own live or
   hosted receipt exists — this framework never sets it true.
5. Run `python3 -m json.tool` on the new file and `git diff --check`
   against `origin/development`.
6. Checkpoint the owning `issue/*` branch. Do not open a delivery PR.

## Recovery

If a filled record is wrong, revert the documentation/evidence checkpoint
on the issue branch. Vendor bytes, live servers, and completed packet
evidence are out of scope for that revert.
