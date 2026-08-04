---
name: canary-echo
description: "Stage lifecycle canary that echoes tokens via packaged text-echo under sealed Eval Runner certification. No durable shared/repo/network side effects; workspace-scoped tool writes and mandatory ledger telemetry only."
usage_trigger: "Use when proving the certification pipeline or verifying sealed executor receipts with a deterministic echo."
version: 0.2.0
release_tag: v0.2.0
created: 2026-08-03
author: LiNKskills Library
tags: [canary, certification, echo, lifecycle]
engine:
  min_reasoning_tier: fast
  preferred_model: gpt-4o-mini
  context_required: 8000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [text-echo]
permissions: [fs_read]
scope_out: ["Do not perform network calls", "Do not mutate repositories or shared state", "Do not claim certification without sealed executor receipts"]
format_profile: simple
last_updated: 2026-08-03
---

# canary-echo

> **Profile: `simple`.** Stage lifecycle canary. Single-pass and stateless with respect to
> shared systems. Invokes packaged `tools/text-echo` only (`side_effect_class: none`).
> Telemetry ledger append remains mandatory.

## Side-effect boundary (precise)

| Allowed | Forbidden |
|---|---|
| Packaged `text-echo` stdout (no durable mutation) | Network calls |
| `write_file` / workspace tools **only** inside the ephemeral sealed eval workspace | Mutating the git repo, shared stage state, secrets, or durable host paths outside that workspace |
| Append-only `execution_ledger.jsonl` telemetry (mandatory for every skill) | Claiming “no side effects” while skipping ledger telemetry |

“No side effects” here means **no durable shared/repo/network mutation**. Ephemeral
workspace writes during sealed eval and ledger telemetry are expected and in-bounds.

## Preconditions (Fail-Fast)
1. Intelligence floor check: confirm the active runtime satisfies `frontmatter.engine`.
2. Tooling policy check: plan must follow the CLI-first protocol below.
3. Confirm a concrete echo token or JSON payload is provided; otherwise stop and request it.

## Canary Pass (Single Pass)
1. Resolve packaged tool `text-echo` (version `1.0.0`) via CLI-first discovery.
2. Echo the requested token exactly once (plain or `--json` mode as specified).
3. Return the tool stdout unchanged. Do not invent output without an executor receipt.
4. Refuse any request that requires network, secrets, or repository mutation.

## Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: prefer packaged `tools/text-echo` CLI entrypoint.
2. **Level 2 - CLI Wrapper Scripts**: optional helpers under `scripts/` may normalize argv only.
3. **Level 3 - Direct API**: forbidden for this canary.
4. **Level 4 - MCP**: forbidden for this canary.
- When the skill is Generalist or has >10 tools, call `get_tool_details` and cache capability summaries before use.

## Ledger (Telemetry — mandatory)
On completion, append `{ "timestamp", "skill", "task_id", "status", "summary" }` to the
root `execution_ledger.jsonl`. Telemetry is required for every skill regardless of profile.
`task_id` here is a lightweight ledger correlation id, not a resumable state handle.

## Contracts
| Direction | Schema Reference | Purpose |
| :--- | :--- | :--- |
| **Input** | `./references/schemas.json#/definitions/input` | Validate echo request. |
| **Output** | `./references/schemas.json#/definitions/output` | Validate echo response. |

## Progressive Disclosure References
- Advanced notes: `./advanced/advanced.md`
- API specs: `./references/api-specs.md`
- Failure archive: `./references/old-patterns.md`
- Change history: `./references/changelog.md`
