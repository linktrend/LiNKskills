# ADR 0005 — Tool Execution Binding and Host Authority for Permission-to-Act

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §11, §20.2)
- **Context source:** Plan §11 (tool architecture), §20.2 (access vs permission-to-act), ADR 0001 (no LiNKskills governance / permission-to-act)

## Context

Skills depend on packaged tools, host capabilities, and external services. Without exact version/hash binding, a “certified” skill can silently pick a different tool binary or placement. Without a hard host-authority rule, LiNKskills risks reintroducing permission-to-act under the guise of tool invocation.

ADR 0001 permanently removed governance from this repo. Tool architecture must reinforce that boundary.

## Decision

**1. Every packaged tool has a versioned descriptor** declaring: stable tool ID and semantic version; source and bundle hashes; input/output JSON schema; command/transport entrypoint; supported platforms and runtime requirements; side-effect class and reversibility; secrets/capabilities required (names only); network/filesystem boundaries; timeout, retry, and idempotency; verification/smoke tests; owning skill(s) and reverse dependencies; compatibility and deprecation state.

**2. Exact hash resolution is mandatory.** Every invocation resolves to an exact tool version/hash and certified execution profile. No floating “latest” substitution in certified runs. Material tool changes move affected profiles to compatibility-check / `eval_pending` until required regressions pass; unaffected profiles stay usable.

**3. Execution placement is recorded and certified.**

- Repository, filesystem, local browser, and local-development tools default to the actor host.
- Centralized data/services may run through a server-side adapter.
- The execution profile records which placement was certified.
- The host enforces approval and operational authority.

**4. Host / Program authority owns permission-to-act.** LiNKskills may control access to its own draft/private/eval content and tool service. It identifies procedural capability and exact tools. It never grants Program permission, issues leases, or bypasses host Program/runtime controls. Side effects require independent host/Program approval.

**5. MCP exposure distinguishes control plane from packaged tools.** Stable `skills_*` operations handle discovery, runs, validation, feedback, and tool resolution. Packaged tools use dynamic registration where supported, or a generic versioned invocation endpoint otherwise. Annotations must accurately state read-only, destructive, idempotent, and external-side-effect behavior.

## Consequences

- Certification evidence must include toolchain hashes, not skill ID alone.
- Consumers fail closed on exact-tool / profile incompatibility.
- Tool ownership stays split: skill wrappers in LiNKskills; reusable app components in LiNKlibraries; host-native capabilities mapped by capability; third-party services via versioned adapters.
- Reintroducing entitlements, leases, kill-switches, or Program grants into LiNKskills remains forbidden (ADR 0001).
