# ED-05 Lisa / OpenClaw owner packet

- **Status:** source-only, disabled by default, not live
- **Packet:** `configs/consumer-activation/ed-05-lisa-openclaw-owner-packet.json`
- **Fragment:** `configs/fragments/ed-05-openclaw-skills.mcp.json.fragment`
- **MCP server name:** `linkskills-ed05-lisa`

## Ownership

LiNKskills authors the packet. OpenClaw Prime / Lisa owns XP-04 managed MCP,
plugins, profiles, and credentials. This repository does not mutate OpenClaw.

## Contract

Provider `skills.api.v0.2` resource-first retrieval. Tools are verify / use-report
/ feedback / librarian status only. Legacy execution operations are denied.
Auth: `platform.auth-claims/1.1.0`, envelope `0.1.0`, audience `lskills-api`,
scope `lskills`. Do not reuse Brain tokens.

## Rollback

Disable the Skills MCP server in OpenClaw-owned config. Retain local bootstrap
skills. Provider publication is unchanged.
