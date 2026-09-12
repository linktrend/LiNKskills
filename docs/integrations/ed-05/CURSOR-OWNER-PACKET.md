# ED-05 Cursor owner packet

- **Status:** source-only, disabled by default, not live
- **Packet:** `configs/consumer-activation/ed-05-cursor-owner-packet.json`
- **Fragment:** `configs/fragments/ed-05-cursor-skills.mcp.json.fragment`
- **MCP server name:** `linkskills-ed05-cursor` (never a Brain server name)
- **Global Cursor mutation:** false — do not edit `~/.cursor/mcp.json`

## What the owner applies (when XP-02 is authorized)

Copy the disabled fragment into the **project-scoped** MCP surface only after
replacing SecretRef **file paths** (never paste keys). Keep `disabled: true`
until the canary owner explicitly enables it. Exact URLs, scopes, versions,
digests, tool authority, telemetry bounds, and rollback are in the packet —
do not invent them.

## Pins

The five ED-04 internal releases (`git-safeguard@1.1.0`, `persistent-qa@1.0.0`,
`repository-manager@1.0.0`, `skill-template@1.2.0`, `tool-architect@1.0.0`)
with the published bundle and package digests.

## Brain vs Skills

Skills PACI client, audience `lskills-api`, and this MCP name stay separate
from Brain credentials, Brain MCP entries, and Brain transcripts.

## Rollback

Disable or remove the project-scoped entry. Retain local bootstrap skills
`agentsetup@1.3.0` and `agentcomply@1.3.0`. Provider publication is unchanged.
Do not rotate Platform credentials from Skills.
