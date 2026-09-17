# LiNKskills — Current operational notes

**LiNKskills 1.0 release:** protected `development`, `staging`, and `main` are aligned to commit `e40bf0dac697eca74a49d956189d2a87f728fbd6`, tree `d5b3410ccf4a383fba71ace86e8904a6dceb1270`. The production target is Server 01.

This file now records only work that belongs after the 1.0 source release. Historical build packets, stale blockers, and completed issue reconciliations are in [`archive/`](archive/). Do not reopen archived plans because an old document says “pending”.

## External operational ownership

- **Server 01:** runtime deployment/readback, image and source pin, service lifecycle, backup/restore, rollback, and production health.
- **LiNKplatform:** live shared migrations, PACI issuer/JWKS/introspection, capability grants, and generic Librarian host scheduling.
- **Consumers:** actor-specific host configuration and bindings for OpenClaw Prime, Codex, Cursor, and LiNKautowork.

## LiNKskills maintenance

- Keep the catalog index current when skills change.
- Require executable evaluation evidence before publishing a new release.
- Preserve the exact source commit/tree in every deployment and rollback receipt.
- Keep the compatibility checkout path until all consumers have migrated to Gateway/MCP.
- Treat contract version changes as compatibility releases; do not silently change frozen Platform contracts.

For the complete operating model, read [`LINKSKILLS-AGENT-GUIDE.md`](LINKSKILLS-AGENT-GUIDE.md).
