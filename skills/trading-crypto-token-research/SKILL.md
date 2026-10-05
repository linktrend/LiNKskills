---
name: trading-crypto-token-research
description: "Research token supply, unlocks, protocol economics, holder coverage, chain risks, and conditional valuation using supplied dated evidence."
usage_trigger: "Tokenomics, circulating supply, unlocks, holder concentration, protocol value capture, or crypto asset research."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library (draft)
tags: [trading, crypto, research, jane, draft]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No wallet interaction, transaction, order, or trade execution.", "No credentials, paid service, RPC, or API assumed.", "No address ownership or malicious intent inferred from heuristics.", "No price-impact or valuation claims from generic thresholds.", "No runtime JSON state or source script execution."]
format_profile: simple
last_updated: 2026-10-05
---
# Crypto token research

**Status:** isolated unqualified task draft. Jane may give a conditional advisory view when the user requests it and the evidence supports it. No recommendation authorizes an order or external action.

Frontmatter `read_file` and `write_file` are portable logical aliases for the host's native persistent-session read/write capability, not promises that tools with those names exist. Use the supplied inline schemas for schema discovery. Do not invoke `read_file` or `write_file` by name unless those exact tools are exposed. Call `get_tool_details` only if the host actually exposes it and additional detail is needed.

## Inputs

Use the actual inline schema in `references/schemas.json#/definitions/input`. Require network and canonical asset identifier, decimals, as-of timestamp, immutable source snapshot, source coverage, and explicit supply definition. Add dated unlock, fee/revenue, holder, authority, liquidity, and comparable inputs only when relevant. Missing identity or denominator prevents relevant calculation; missing optional economics permits a bounded partial result.

## Method

1. Confirm network, canonical mint/contract, token standard, decimals, point-in-time and source vintage. A ticker or symbol alone is not identity.
2. Reconcile supply definitions by source row: issued/minted, burned, reported circulating, vesting/locked, treasury, staked, bridged, and maximum. Do not assume staked or treasury units are non-circulating; label the source's definition and show unreconciled balances.
3. For dated emission/unlock scenarios, calculate token quantities and value only from supplied prices and schedule data. Compare to explicitly named volume/liquidity windows as descriptive ratios. Do not translate a ratio into a drawdown without a separately supported empirical model.
4. Separate gross activity, protocol fees, net revenue, treasury receipts, burns, buybacks, and token-holder entitlements. A valuation multiple called P/E is inappropriate without evidenced equity-like earnings rights; distinguish activity multiples from cash flows.
5. Calculate holder metrics only on an explicit observed sample and denominator. Disclose missing coverage, exclusions, program accounts, and snapshot date. Gini/HHI/Nakamoto values from truncated lists are sample measures, not proof of decentralization or ownership.
6. Describe early buys, shared funders, creator balances, authority settings, and vendor risk scores as observations or hypotheses. Do not call addresses insiders, coordinated, or malicious without independently verified identity and evidence.
7. Keep chain-specific mechanics optional. Pump.fun calculations require current official program/version/layout, exact integer units, fee and rounding conventions, and independently checked fixtures. Until supplied, omit decoding and calculations.
8. Give counterevidence, unresolved gaps, and a conditional advisory stance or `no_view`. Separate sourced facts, calculated values, assumptions, and hypotheses.

## Tools and state

The portable read_file/write_file labels map only to the host’s native persistent-session read/write capability; JSON schemas are supplied inline. A direct API, native CLI, CLI wrapper, or MCP route may be used only if the active host actually exposes and authorizes it. The schema is inline, so do not invoke a named discovery tool that the host does not expose. Tool names in source materials do not prove a connected API, provider, RPC, credential, or paid entitlement. Validate actual supplied JSON structurally; structural validation cannot qualify the analysis. Carry continuity in the single native session. Do not create JSON/JSONL state sidecars. Eric owns LiNKtrading adapters; Sara owns legal/accounting conclusions.

## Sources

`references/upstream/` contains selected MIT-licensed source Markdown, exact-byte copies segregated as data-only; `SKILL.md` copies are named `SKILL.source.md` to prevent skill discovery. Source scripts were not copied or run. See `references/source-provenance.json` for commit, path, hash, notice, and exclusions. The upstream LLMQuant crypto workflow remains unread and excluded.

## Outputs and checks

Return the task-specific fields in `references/schemas.json#/definitions/output`; use `examples/worked-example.json` only as a fictional shape. Proposed adversarial cases in `references/eval-suite.json` are not run. No provider facts or method qualification are claimed.
