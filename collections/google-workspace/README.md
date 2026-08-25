# Google Workspace vendor collection

This directory is the PKT-05 immutable metadata envelope for the mechanically
inventoried Google Workspace CLI skills. The preserved vendor bytes are under
`vendor-skills/google-workspace/`; this collection does not copy the CLI binary,
credentials, account bindings, or connector implementation.

## Exact source and review

- Publisher/repository: Google Workspace CLI, `https://github.com/googleworkspace/cli`
- Reviewed source: `main` at commit `a3768d0e82ad83cca2da97724e46bea4ff0e6dbd`
- Source tree: `28127e4c0edff4bdf9226369e7a2ef744b353c25`
- Inventory: 95 top-level `skills/*/SKILL.md` entries
- Licence: Apache-2.0; attribution and the upstream notice remain required
- Historical provenance: local `v0.18.1` at `e9970db26fb32ca97f11ce0d8c7c53e4eedd81cc`

`collection-manifest.json` binds the complete inventory. Every member has a
vendor release record, exact-resource descriptor, and fail-closed eligibility
record. The collection and every member remain `unqualified` and inactive by
default. `role-pack-manifest.json` is reference-only metadata for Lisa's seven
Workspace families; its activation is permanently false until consumer-owned
authority and all independent gates exist.

The imported `SKILL.md` files are preserved unchanged. Administrative, write,
sharing, deletion, download, subscription, and Model Armor entries are retained
for review but remain nonselectable; no adaptation silently overwrites vendor
bytes. `update-candidate.json` is a pending, non-promoting proposal from the
historical `v0.18.1` snapshot to the reviewed commit and cannot change a current
pointer.
