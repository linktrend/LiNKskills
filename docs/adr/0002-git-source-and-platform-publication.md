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
