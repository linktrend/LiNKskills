# Frozen Interfaces

These interfaces convert settled requirements into implementation constraints. An executor reports a blocker instead of renaming, merging, or weakening them.

## 1. Release identity and lineage

Every release is identified by `skill_id`, semantic `version`, `inventory_digest`, `content_digest`, and immutable artifact digest. External releases also carry `publisher`, `repository`, `source_ref`, `source_commit`, `source_path`, `retrieved_at`, `licence`, and per-resource provenance.

Release kinds are `native`, `vendor`, and `adapted`. An adapted release has an immutable `upstream_release_id`; it never overwrites vendor bytes. A collection manifest binds exact member releases and digests.

Lifecycle/selectability states must distinguish at least draft/eval-pending/qualified, deprecated, superseded, withdrawn, quarantined, rejected, incompatible, and unqualified. Only approved qualified compatible releases are ordinarily selectable.

## 2. Taxonomy and discovery

The provider-owned hierarchy is `family -> subcategory -> optional nested group -> exact release`. Vendor service/helper/persona/recipe labels are secondary metadata. Family and category responses contain identifiers, one-line descriptions, counts, and pagination only. Skill instructions/resources are returned only after exact selection and authorization.

## 3. Eligibility decision

Eligibility is the intersection of:

`platform_technical_eligibility AND skills_release_selectability AND consumer_profile_activation AND consumer_tool_authority`

No term substitutes for another. Awareness metadata is not selectability; selectability is not activation; activation is not technical authority.

## 4. MCP contract

The intended consumer path uses standard MCP initialize/capability negotiation, bounded catalogue resources, and exact-release resource reads. The provider does not execute consumer work. Legacy list/search/describe/fragment/release may exist only behind a measured migration adapter; `skills_run_*` and `skills_tool_*` are prohibited from the intended Lisa architecture.

## 5. External update candidate

LiNKautowork is the recommended deterministic poller/diff producer. It submits a signed, idempotent candidate containing upstream identity, old/new refs, inventory/content digests, licence finding, and diff reference. LiNKskills owns validation, review state, evaluation, recommendation, qualification, release, and rollback. No poll result changes a current pointer or activation automatically.

## 6. Template authority

LiNKskills owns reusable schemas, required sections, validation, omission/decision logic, and generic defaults. OpenClaw instance overrides contain bindings and editable wording only and must validate against the exact skill release schema.

## 7. Mutable state

- OpenClaw private SQLite mints canonical `T-` task references and owns Lisa private task, health, battery, and selfie state.
- Google Tasks, Brain records, Program Ledgers, messages, and handoffs retain their own opaque references mapped to the `T-` reference.
- LiNKskills owns no consumer task or health state.

## 8. Role-pack shape

A role pack is an immutable manifest of exact qualified release references, constraints, required capability classes, compatibility, and applicability. It is not a skill body, identity profile, credential bundle, activation record, or mutable pin set.

## 9. Proof levels

`source`, `consumer`, `hosted/stage`, `VPS`, `E2E`, and `production` are distinct evidence classes. A lower class never proves a higher class. Every receipt binds repository, commit, tree, command/profile digest where applicable, and result.

## 10. Approval and rollback

Checkpoint commits are automatic under the protocol. Main promotion, release publication, production deployment, protection changes, provider-live mutation, live migrations, collection activation, and agent activation require recorded authority. Rollback restores a previously qualified exact release or prior consumer pin; it never mutates an immutable release.
