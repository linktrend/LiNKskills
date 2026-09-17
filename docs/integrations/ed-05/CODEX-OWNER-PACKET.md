# ED-05 Codex owner packet

- **Status:** source-only, disabled by default, not live
- **Packet:** `configs/consumer-activation/ed-05-codex-owner-packet.json`
- **Fragment:** `configs/fragments/ed-05-codex-skills.config.toml.fragment`
- **MCP server name:** `linkskills_ed05_codex` (must not collide with Brain MCP names)

## Ownership

LiNKskills authors this packet. LiNKbrain / XP-03 applies shared Codex
`config.toml` only when authorized. Skills agents must not edit the host.

The fragment ships with `enabled = false`. Keep Skills credentials, audience
`lskills-api`, and scope `lskills` out of Brain config and out of Git.

## Pins and deny

Exact ED-04 five-Skill pins. Deny native Codex substitutes, stale cache,
similar-name skills, latest pointers, catalog expansion, and legacy
`skills_run_*` / `skills_tool_*`.

## Rollback

Remove or keep the Skills MCP entry disabled. Retain local bootstrap
`agentsetup@1.3.0` / `agentcomply@1.3.0`. Provider state is unchanged.
