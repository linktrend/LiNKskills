# ED-05 source-only consumer packets

LiNKskills owns three **disabled-by-default** owner packets for the qualified
initial five Skills. This deliverable is **not live**. Consumer owners apply
their own files. This packet does **not** activate consumers, mint live tokens,
publish providers, deploy, or edit external consumer repositories.

| Owner packet | Consumer | Fragment | Apply owner |
|---|---|---|---|
| `configs/consumer-activation/ed-05-cursor-owner-packet.json` | Cursor | `configs/fragments/ed-05-cursor-skills.mcp.json.fragment` | XP-02 / project-scoped Cursor owner |
| `configs/consumer-activation/ed-05-codex-owner-packet.json` | Codex | `configs/fragments/ed-05-codex-skills.config.toml.fragment` | XP-03 / LiNKbrain host owner |
| `configs/consumer-activation/ed-05-lisa-openclaw-owner-packet.json` | Lisa/OpenClaw | `configs/fragments/ed-05-openclaw-skills.mcp.json.fragment` | XP-04 / OpenClaw Prime |

Exact release/digest pins: `configs/consumer-activation/ed-05-initial-five-pins.json`, bound to accepted ED-04 receipt `sha256:c2ac495dd9feee1257f022a16ae9aea55ee9256a3d1debc43fcb4b4164e79b42` at development `0d4ad748ff9d4d89911f20e0c01aca0e1107fc54` / tree `6944fe1676beba87a44825f29a13e440f8f3512c`.

Later expansion manifests under `configs/consumer-activation/*-internal-canary.json` remain disabled. Client package (`packages/client/`) is ED-02-owned and is not edited here.

## Required fake-contract flow

1. Private Skills provider v2 fixture endpoint (`liveUrl` is null).
2. Platform token mint: `client_credentials` + `private_key_jwt`, audience `lskills-api`, scope `lskills`. Brain credentials and `lbrain-api` are denied.
3. Retrieve the exact pin; verify bundle and package digests.
4. Execute locally under consumer tool authority. Provider does not execute.
5. Submit a bounded `use-report-v0.2` (opaque correlations only).
6. Fail closed on deny, stale cache, similar name, native substitute, latest pointer, or legacy `skills_run_*` / `skills_tool_*`.
7. Rollback disables the consumer pin, retains local `agentsetup@1.3.0` / `agentcomply@1.3.0`, and leaves provider state unchanged.

Owner notes: [CURSOR](./CURSOR-OWNER-PACKET.md), [CODEX](./CODEX-OWNER-PACKET.md), [LISA/OpenClaw](./LISA-OPENCLAW-OWNER-PACKET.md).
