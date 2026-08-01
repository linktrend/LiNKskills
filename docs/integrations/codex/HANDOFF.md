# Codex Handoff — LiNKskills Skills MCP Fragment

- **Status:** Fragment + conformance ownership handoff (**immutable Skills deliverable**)
- **Date:** 2026-07-27 (refreshed 2026-07-30 — ownership/immutability note only)
- **Fragment:** `configs/fragments/codex-skills.config.toml.fragment`

## Ownership

| Asset | Owner |
|---|---|
| Independently named Skills MCP fragment + Skills conformance tests | **LiNKskills** |
| Shared Codex `config.toml` / host hooks application | **LiNKbrain** (default shared Codex host owner) |

## Immutable fragment rule (2026-07-30)

The Skills Codex fragment in this repository is an **immutable handoff artifact**.

- LiNKskills authors and versions the fragment here for the host owner to consume.
- LiNKskills agents **must never** edit shared Codex host configuration (Brain-owned `config.toml`, hooks, or live MCP registration) from the Skills repo or a Skills session.
- Host apply, credential injection, and enablement remain with the Codex host owner (LiNKbrain by default).
- When AuthClaims / audience pins change, Skills updates **only** this fragment + Skills conformance proofs, then notifies the host owner — Skills still does not mutate the live shared host.

## Delivered by LiNKskills

- `configs/fragments/codex-skills.config.toml.fragment` — independently named `mcp_servers.linkskills_skills` entry (no secrets).
- MCP/gateway conformance coverage under `tests/mcp_server/` and `tests/gateway/`.
- Auth spoof-rejection and HTTP/MCP `skills_list` parity proofs.
- Consumer AuthClaims pin: `platform.auth-claims/1.1.0` / `@linktrend/platform-contracts@0.2.2` (see `docs/contracts/frozen/platform-auth-claims-v1.1.0.CONSUMER-PIN.md`).

## Expected from LiNKbrain owner

1. Review the fragment for naming collisions with Brain MCP entries.
2. Apply into the shared Codex host config only when ready.
3. Notify LiNKskills so Skills-side validation can run against the configured host.
4. Keep credentials out of the fragment; use Platform-issued env injection.

## Explicit non-goals

- No LiNKskills agent mutation of shared Codex files merely to set up development.
- No combined Brain/Skills credential or MCP surface.
- No Skills-claimed live Codex host certification from fragment authorship alone.
- No inventing stage Codex endpoints in Skills docs.

## Related packets

- Stage readiness: `docs/handoffs/2026-07-30-linkskills-stage-readiness-packet.md`
- Librarian stage packet: `docs/handoffs/2026-07-30-linkskills-librarian-stage-packet.md`
