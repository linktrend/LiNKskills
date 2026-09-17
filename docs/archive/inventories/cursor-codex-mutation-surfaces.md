# Cursor and Codex Mutation Surfaces

- **Status:** Phase 0 inventory (accepted)
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §21.2–21.3, §29.2, Phase 0 items 6 / 15

## Purpose

Name every shared/global Cursor and Codex mutation surface that concurrent Grok agents might touch, assign a sole owner, and reserve LiNKskills to the Cursor product canary (prefer project scope).

## 1. Cursor surfaces

| Surface | Scope | Sole mutation owner | LiNKskills role |
|---|---|---|---|
| LiNKskills project MCP config (repo-local / isolated canary) | Project | **LiNKskills** | Own/implement canary |
| LiNKskills Cursor integration template, fixtures, diagnostics | Repo docs/tests | **LiNKskills** | Own |
| Shared IDE Development `.cursor` symlink target | Shared across repos | **None casually** — maintenance gate only | Do not edit for setup; document stale identity instructions only |
| User-level Cursor MCP (`~/.cursor/mcp.json` or equivalent) | Global | Maintenance-gated; prefer avoid | Stop + coordinated window if unavoidable |
| User-level Cursor rules, hooks, extensions, settings | Global | Maintenance-gated | No change for environment setup |
| Other agents’ project Cursor configs (Brain/Platform/OpenClaw) | Their repos | Owning repo agent | No change |

**Cursor canary preference:** project-scoped / isolated configuration. Using Cursor as the development IDE grants no authority over shared/global Cursor settings.

### Shared `.cursor` identity drift (documented; do not “fix” by editing the symlink target)

Observed 2026-07-27 on this checkout:

- `LiNKskills/.cursor` is a symlink to `../IDE Development/.cursor` (shared across repos).
- Shared rule `rules/01-identity.mdc` states this repository is **LiNKdeveloper** (`IDE Development` on disk).
- When Cursor loads that shared identity rule through the LiNKskills symlink, agents can misidentify **LiNKskills** as LiNKdeveloper and apply the wrong ownership/product boundaries.

Disposition for Phase 0+:

- Treat the drift as a known preflight defect (plan §7.6 / Phase 0 item 6).
- Do **not** edit the shared symlink target or rewrite shared identity rules merely to set up a Skills session.
- Isolate the LiNKskills product canary with project-scoped configuration.
- Any change to the shared IDE Development `.cursor` surface requires the Cursor maintenance gate below.

**If global mutation is unavoidable (§21.2):**

1. Stop before changing.
2. Document exact mutation, affected active agents, validation, and rollback.
3. Obtain a coordinated maintenance window.
4. Confirm the other three Grok sessions will not be disrupted.
5. Apply and verify only inside the window.
6. Record result and restoration path in the implementation handoff.

## 2. Codex surfaces

| Surface | Scope | Sole mutation owner | LiNKskills role |
|---|---|---|---|
| Shared Codex `config.toml` (user or trusted shared project) | Shared host | **LiNKbrain** (default for this four-agent rollout) | Supply independently named Skills fragment; do not edit shared file |
| Common Codex hooks / lifecycle scripts | Shared host | **LiNKbrain** (default) | Supply Skills-specific requirements/tests only |
| Independently named Skills MCP fragment + conformance suite | LiNKskills-produced artifact | **LiNKskills** authors; shared owner applies when ready | Own fragment + validate configured Skills behavior |
| Brain MCP fragment | Brain-produced | **LiNKbrain** | No change |
| Project-local Codex config used only by Skills canary (if created) | Skills-isolated | **LiNKskills** only if truly non-shared | Prefer not to create a second competing shared host |

If the Principal later assigns a dedicated Codex integration agent, that assignment supersedes the LiNKbrain default for shared host configuration. Ownership of the shared file does not become concurrent.

## 3. Related non-Cursor/Codex surfaces (for collision awareness)

| Surface | Sole owner |
|---|---|
| OpenClaw/Lisa managed MCP, plugins, hooks, buffers, profile | OpenClaw Prime |
| Platform actor credentials / GSM secrets for consumers | LiNKplatform |
| `LiNKplatform/packages/librarian-runner` shared files | LiNKplatform |

## 4. Acceptance for this session

- Cursor product-canary changes are reserved to LiNKskills, prefer project scope.
- Shared Codex host configuration is reserved to the default LiNKbrain integration owner.
- No LiNKskills Phase 0 work may mutate shared/global Cursor or shared Codex configuration merely to set up the development environment.
