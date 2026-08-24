# Governed Skill Expansion Baseline Inventory

- **Packet:** PKT-00 / ISS-00
- **Observed:** 2026-08-24 (Asia/Taipei)
- **Repository:** `linktrend/LiNKskills`
- **Scope:** source, contracts, provider, catalogue, Librarian, Google Workspace snapshot, and consumer handoff surfaces
- **Evidence class:** source only; this inventory does not claim consumer, hosted/stage, VPS, E2E, or production proof.

## Exact Git and IDE baseline

The committed execution manifest and routing receipt remain bound to the following
planning identity:

| Identity | Commit | Tree | Role |
|---|---|---|---|
| Manifest-bound execution baseline | `2896fd89726f0b20258ec5a7bba55ccc6299ceb6` | `727694a95c83678bd6c7be7da2c5b26127b49e6e` | Required manifest/receipt identity |
| Current `origin/development` candidate | `91970bbb273acd12a643c722608ded33e42ae7e4` | `5312f355243bda6452422a262e18135cb2c07372` | Descendant used by this issue worktree |
| IDE Development v2.5.1 source identity | `ded1baa63939db92f7616ac7393401a702d881de` | `d03e551d9c0189a3f22d67663a53cb68235f3c1d` | Recorded in the 2026-08-21 planning handoff |

The current candidate is an ancestor-compatible descendant of the manifest baseline.
The managed package surfaces are unchanged across `2896fd8..91970bb` (no diff under
`.ide-development/`, `core/managed-core/`, `.agents/`, `AGENTS.md`, or `scripts/`).
This proves package continuity, not a new manifest identity. Before PKT-01, the
orchestrator must either refresh the manifest and issue a new digest-bound routing
receipt for `91970bb…`, or record an explicit approval to execute against the older
manifest baseline. This packet does not edit the manifest, matrix, or receipt.

The current manifest and companion digest values are:

- `EXECUTION-MANIFEST.json`: `sha256:c14c3ccdb612d9bee2be2a4d4ff71358e98cff63e6f09c9f58ac9e49816e7263`
- `MODEL-ROUTING-MATRIX.json`: `sha256:5877168e5ba0e8523fe6ce765548525e2eabf707944f161f7f1cac55a64c287f`
- `MODEL-ROUTING-SUCCESSOR.md`: `sha256:3befce649789720a8180313d1a5587da8634fbc05f6e52999b3f7cdf89e96ef9`

## Surface reconciliation

| Surface | Source evidence at current candidate | PRD classification | Result / gap |
|---|---|---|---|
| Editable catalogue | `skills/` contains 35 first-level skill directories; `catalog/index.json` contains 35 entries, `git_sha` `af70f7ff…`, and all 35 report `draft` | 35 skills retained; `canary-echo` described as usable in the PRD baseline | **Reconcile:** the index is all-draft, so the PRD's usable count is not proved by the current index. PKT-01/PKT-04 must use a fresh certification receipt, not file presence. |
| Legacy source manifest | `manifest.json` contains 53 entries: 34 `skill` and 19 `tool` records | Existing catalogue/tool foundation retained | **Retained compatibility surface:** the manifest is not the governed v2 catalogue authority. |
| Provider-v2 | `packages/mcp_server/linkskills_mcp/v2_provider.py` exists beside the server and stdio adapter | Resource-first provider-v2 foundations retained; actual v2 path incomplete | **Implemented but incomplete:** MCP negotiation, bounded family discovery, exact release bytes, and provider-side execution retirement remain PKT-02. |
| Contracts and schema | `packages/contracts/schemas/` contains 20 JSON schemas, including release, skill-pack, fragments, MCP envelope/policy, execution profile, and provider metadata | Release/digest/attestation and progressive-disclosure foundations retained | **Gap:** taxonomy, collection, vendor/adaptation lineage, update candidate, eligibility, and role-pack schemas are PKT-01. |
| Publisher/release | `packages/publisher/` contains bundle, registry, migration, and release-v2 modules | Immutable release and publication foundations retained | **Gap:** external vendor bytes, linked adaptations, collection manifests, candidates, and rollback lifecycle are PKT-03. |
| Librarian | `packages/librarian_domain/linkskills_librarian/` contains worker, policy, store, conformance, and telemetry modules; domain contract is `docs/contracts/librarian-domain-worker-v0.1.md` | Librarian review-queue foundations retained; update-diff outcomes incomplete | **Boundary confirmed:** Skills owns domain worker logic/contracts; Platform owns generic host/shared runner integration (ADR 0008). |
| Google Workspace source | `tools/gws/` wrapper is pinned to fork commit `e9970db26fb32ca97f11ce0d8c7c53e4eedd81cc`, release `v0.18.1`; historical vendor tree has 93 top-level `skills/*` directories | Controlled wrapper and historical snapshot retained; complete reviewed collection is new work | **Provenance only:** no qualification or activation inferred. PKT-05 must mechanically inventory a newly reviewed upstream commit. |
| Consumer handoffs | Codex, Cursor, OpenClaw integration docs exist under `docs/integrations/`; Platform auth/PACI and Librarian handoff contracts exist under `docs/contracts/` | Cross-repository interfaces exist; consumer/stage/production proof incomplete | **Ownership confirmed:** OpenClaw owns local retrieval/execution and private state; Platform owns identity, shared migrations, and host integration. |
| Live/runtime proof | No source file in this inventory is a hosted, VPS, E2E, or production receipt | PRD definition of done requires separated proof classes | **Held outside PKT-00:** no runtime or deployment claim is made. |

## Ownership and supersession findings

1. LiNKskills owns reusable skill source, release metadata, taxonomy, qualification
   evidence, and provider contracts. LiNKplatform owns identity, technical claims,
   shared live migrations, and generic Librarian hosting. LiNKautowork may poll and
   submit candidates; it may not qualify or promote. OpenClaw owns consumer profiles,
   local execution, activation, schedules, and private state.
2. Vendor labels and source paths remain provenance metadata beneath the single
   provider taxonomy. They must not become a second top-level discovery authority.
3. Existing release/digest/attestation primitives are extended by PKT-01/PKT-03;
   they are not duplicated or silently replaced.
4. The `gws` binary/account connector, Odoo connector, consumer schedules, private
   SQLite state, and host configuration remain outside LiNKskills product ownership.

## Reconciliation commands

The following read-only commands produced the evidence above:

```text
git rev-parse origin/development
git rev-parse 2896fd8^{tree}
git diff --quiet 2896fd8..91970bb -- .ide-development/ core/managed-core/ .agents/ AGENTS.md scripts/
jq '.skill_count, (.skills|length), .git_sha, .source_tree_sha256' catalog/index.json
jq '[.skills[].certification_state] | group_by(.) | map({state:.[0], count:length})' catalog/index.json
jq '[.[] | select(.type=="skill")] | length' manifest.json
find tools/gws/vendor/link-gws-cli/skills -mindepth 1 -maxdepth 1 -type d
sha256sum docs/planning/governed-skill-expansion/EXECUTION-MANIFEST.json docs/planning/governed-skill-expansion/MODEL-ROUTING-MATRIX.json docs/planning/governed-skill-expansion/MODEL-ROUTING-SUCCESSOR.md
```

## Exit condition

PKT-00 may record this source reconciliation and the architecture amendments. PKT-01
is **HOLD** until the exact manifest/receipt baseline mismatch is resolved by the
orchestrator with a fresh digest-bound identity or explicit approval of the existing
manifest identity. No product code, migration, catalogue generation, provider
deployment, consumer activation, publication, or promotion is authorized by this
inventory.
