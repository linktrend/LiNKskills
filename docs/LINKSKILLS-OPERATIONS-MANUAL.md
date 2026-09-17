# LiNKskills 1.0 Operations Manual

**Current source identity:** `main` commit `e40bf0dac697eca74a49d956189d2a87f728fbd6`, tree `d5b3410ccf4a383fba71ace86e8904a6dceb1270`.

LiNKskills is the shared catalog, evaluation, publication, Gateway/MCP, telemetry, and Librarian domain service. This manual is the short operational reference. The complete agent-facing explanation is [`LINKSKILLS-AGENT-GUIDE.md`](LINKSKILLS-AGENT-GUIDE.md).

## Daily operation

1. Keep `catalog/index.json` generated and current.
2. Require executable evaluation evidence before publishing a skill release.
3. Publish immutable bundles through the Gateway/MCP path.
4. Record usage and feedback; preserve local buffers during store outages.
5. Keep Librarian promotion supervised when evidence is incomplete.
6. Bind every deployment and rollback to an exact commit, tree, release ID, and image digest.

## Production ownership

- **Server 01:** checkout/image, environment secrets, process lifecycle, PostgreSQL connection, health/readiness, backups, restart, rollback, and runtime readback.
- **LiNKplatform:** shared migrations, PACI issuer/JWKS/introspection, capability grants, and the generic Librarian host.
- **LiNKskills:** source, catalog, packages, contracts, evaluation logic, Gateway/MCP, telemetry domain, Librarian domain, and non-secret handoff documents.
- **Consumers:** actor-specific configuration and bindings for OpenClaw Prime, Codex, Cursor, and LiNKautowork.

Use [`runbooks/PRODUCTION_OPERATIONS.md`](runbooks/PRODUCTION_OPERATIONS.md) and [`integrations/server01/`](integrations/server01/) for host operations. Never put credentials in Git and never use local-test authentication on staging or production.

## Release rules

Only `development`, `staging`, and `main` are long-lived branches. Work enters `development` through protected pull requests and is promoted through protected `staging` and `main` pull requests. Temporary issue, phase, review, and promotion branches are deleted after release completion.

For incidents, stop the service or drain it, read the current deployment receipt, restore the previous recorded identity, and use the Server 01 rollback procedure. A changed source tree invalidates old receipts until regenerated.
