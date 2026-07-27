# ADR 0003 — Protocol-Independent Core with MCP and HTTP Adapters

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §5.3, §8, §13)
- **Context source:** Plan §8 (target architecture), §13 (agent-facing MCP/API), §5.3 (Brain/Skills separation), ADR 0001

## Context

MCP is the primary internal agent interface for Cursor, Codex, and OpenClaw, but treating MCP as the product ontology would couple Skill Packs and domain operations to one transport. LiNKbrain and LiNKskills also risk being collapsed into a combined gateway if namespaces, credentials, queues, or telemetry are shared.

LiNKskills needs one domain core callable by multiple adapters, with a hard service boundary from LiNKbrain.

## Decision

**1. Protocol-independent core.** Skill Packs, catalog, discovery, progressive disclosure, tool resolution, run lifecycle, telemetry, feedback, and certification live in a transport-agnostic domain core. MCP and HTTP/API (and future SDK) adapters call the same domain operations; they do not redefine them.

**2. Independently named `skills_*` MCP namespace.** LiNKskills exposes only `skills_*` tools (catalog/disclosure, run lifecycle, tools/verification, feedback). LiNKbrain exposes `brain_*` through its own service. Final operation names may refine plan §13 proposals, but the namespace split is mandatory.

**3. Separate services — no combined Brain/Skills gateway.** LiNKskills and LiNKbrain retain separate services, schemas, MCP/API domains, credentials/scopes, caches, queues, telemetry, retention rules, failure states, and feature flags. There is no combined Brain/Skills Gateway and no shared mutable domain table.

**4. Shared only LiNKplatform cross-cutting contracts.** Actor/organisation claims, correlation IDs, credential/deployment/audit/observability conventions, and the generic Librarian host lifecycle may be shared. Domain data and failure domains must not merge.

**5. Gateway derives identity from credentials.** The LiNKskills Gateway authenticates platform claims, binds domain actor/runtime/run records to platform actor IDs, and never becomes an organisation-wide identity issuer.

## Consequences

- A consumer adapter may connect to both Brain and Skills, but must keep configuration, tools, credentials, health, and rollback distinguishable.
- Cross-service correlation uses opaque IDs and approved outcome references only.
- Domain packages should separate core services from `mcp-server` / HTTP adapters so Skill Packs remain protocol-independent.
- Combined-gateway shortcuts are rejected even if they appear operationally convenient.
