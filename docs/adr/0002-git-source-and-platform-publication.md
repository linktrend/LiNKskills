# ADR 0002 — Git Owns Editable Source; LiNKplatform Owns Published Operational State

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §9)
- **Context source:** Plan §9 (source, publication, storage), §5.1–5.2 (product boundaries), ADR 0001 (catalog + eval + telemetry scope)

## Context

Today Programs pin a LiNKskills Git checkout and load Skill Packs from the filesystem. Optional PostgREST writes hit `lskills` tables, but there is no immutable published-bundle registry, release channel, or one-way publication pipeline. That leaves two competing “truths”: whatever is checked out locally, and whatever happens to be in the database.

LiNKskills must keep Git as the authoring and review system while making published operational delivery run from LiNKplatform-backed registry and storage. Dual steady-state authority would recreate the responsibility bleed ADR 0001 already rejected for governance.

## Decision

**1. Split authority by responsibility (not by duplicate stores).**

| Responsibility | Authority |
|---|---|
| Editable Skill Pack / tool / eval source | LiNKskills Git |
| Review, branches, diffs, source rollback | Git |
| Published skill identity / version / status | LiNKplatform Postgres (`lskills`) |
| Certified immutable bundle | LiNKplatform-backed object storage |
| Search / routing / disclosure fragments | Postgres / cache derived from the bundle |
| Certification / eval evidence | Postgres plus immutable evidence artifacts |
| Runs, events, feedback, quality metrics | Postgres |
| Consumer delivery | LiNKskills Gateway through MCP / API |

**2. Publication is one-way.** Git commit → validate → resolve dependencies → build deterministic bundle → hash source/bundle/eval/tools → execute required eval profiles → record certification → upload immutable bundle/evidence → advance published release transactionally → warm disclosure indexes → emit audit event.

**3. Published bundles are immutable.** A correction creates a new version/release. It never edits an already certified bundle in place. Rollback retargets the channel/default profile to a prior immutable release; it does not mutate history.

**4. No dual steady-state truth.** Adapters may cache the last verified published bundle by content hash during outage, but must report that live freshness could not be checked and must never silently substitute a draft or mismatched version. Legacy Git-checkout loading remains a migration path only, not the steady-state published runtime.

## Consequences

- Consumers integrate against the Gateway and published releases, not a required LiNKskills checkout.
- `lskills` migration source stays a LiNKskills domain asset; LiNKplatform reviews, sequences, applies, and operates shared live migrations.
- Certification and release evidence must reference exact hashes; filesystem checkout alone cannot claim published readiness.
- Source rollback and operational rollback remain distinct: Git reverts editable source; platform channel pointers select known-good immutable releases.

## Amendment — External vendor, adaptation, and update lineage (PKT-00)

- **Status:** Proposed for Principal approval; this documentation amendment does not authorize an importer, migration, publication, or activation.
- **Date:** 2026-08-24
- **Authority:** Governed Skill Expansion PRD §§5–6 and frozen interfaces §5; PKT-00 baseline reconciliation.

### Context

The publication split above establishes immutable Git source and published operational
state, but it does not by itself define how untrusted external collections enter the
catalogue. Treating an upstream checkout as native LiNKskills source would lose
provenance, make adaptation indistinguishable from vendor bytes, and allow an update
poll to become an implicit release switch.

### Decision

External material is represented as a separate, immutable lineage:

1. A vendor release preserves the upstream repository, publisher, source ref/commit,
   source paths, retrieval time, licence findings, inventory digest, and per-resource
   content digests. The original bytes are never edited in place.
2. LiNKtrend changes are published only as separately versioned adapted releases with
   an immutable `upstream_release_id`; an adaptation never overwrites its vendor
   source.
3. An upstream change is a signed, idempotent candidate containing old/new identity,
   inventory/content digests, licence findings, and a diff reference. Candidate
   arrival cannot advance a current pointer or activate a collection.
4. The Skills Librarian reviews candidates and may recommend `accept`, `adapt`,
   `postpone`, or `reject` under ADR 0008's domain-worker boundary. Qualification,
   publication, current-pointer changes, and rollback remain explicit controlled
   transitions.

### Alternatives considered

- **Copy upstream files into `skills/`:** rejected because provenance and immutable
  vendor bytes would be lost.
- **Auto-promote the newest upstream ref:** rejected because polling is not review,
  qualification, or publication authority.
- **Put the lifecycle in LiNKplatform or a consumer:** rejected because LiNKskills
  owns release metadata and curation while Platform owns shared live operations and
  consumers own local execution.

### Consequences and rollback

The lifecycle requires additive release/collection/candidate metadata, review evidence,
and a rollback pointer to a prior qualified immutable release. It creates no new
permission-to-act authority and no live state in this packet. Revert this amendment
before implementation if Principal approval changes; immutable vendor bytes and any
already-published release remain untouched.

### Validation path

PKT-01 must define bounded schemas and negative fixtures before PKT-03 implements the
lifecycle. PKT-03 must then prove provenance, adaptation linkage, candidate idempotency,
review outcomes, and rollback without applying shared live migrations.
