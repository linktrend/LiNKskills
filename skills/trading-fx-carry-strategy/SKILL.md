---
name: trading-fx-carry-strategy
description: "Analyze supplied FX spot, forward, rate differential, volatility and risk context with clear currency/tenor conventions."
usage_trigger: "FX carry, forward points, carry-to-vol context or currency hedge research."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library
tags: [trading, research, jane, draft]
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
scope_out: ["No automatic provider calls, assumed entitlements, credentials, transaction, order or portfolio mutation.", "No invented observations or unqualified backtest/model result.", "No runtime sidecars or source scripts."]
format_profile: simple
last_updated: 2026-10-05
---

# FX carry research

**Status:** isolated unqualified draft, not admitted/published/activated. Jane may offer conditional advisory conclusions when requested and supplied evidence supports them; this method never places orders.

## Capability and inputs

Portable `read_file`/`write_file` labels map to the host's native persistent-session read/write capability; schemas are inline. Do not assume a named API, native CLI, CLI wrapper, MCP, provider, credentials, or paid access. A direct API, native CLI, CLI wrapper, or MCP route may be used only when actually exposed and authorized. Eric owns adapters for the existing LiNKtrading engine. Required task inputs are defined in `references/schemas.json#/definitions/input`; missing identity, date, units, coverage, convention, or source must be reported, not guessed.

## Integrated method

1. Confirm scope, identifiers, as-of and publication dates, unit/currency, source and conventions. Reject mismatched instruments/periods before arithmetic.
2. Calculate only task-relevant metrics from supplied rows using the exact formula and denominator recorded in the output. Keep observations separate from derived values.
3. Preserve incomplete coverage, stale values, missing match, and undefined calculations as unknown; do not rank or infer omitted data.
4. Explain opposing interpretation, basis/convention sensitivity and evidence needed to complete the analysis.
5. Provide conditional research advice only when requested; no external effect. Validate the actual output schema; that is structural validation, not method qualification.

## Source-specific branches

LLMQuant/skills:skills/llmquant-rates-fx/SKILL.md — Router skill for LLMQuant rates and FX workflows. Use when the user needs yield curve, duration, central-bank divergence, FX carry, real-rate, dollar, or cross-currency analysis.

See `references/source-provenance.json` for exact audited path/hash/license and no-copy dispositions. Selected LSEG procedural Markdown is present only as quarantined SKILL.source.md under the root Apache-2.0 license and scoped notice inventory review; this does not qualify the method or grant vendor-data access. Do not assume vendor data tools named by upstream text are exposed.

## Output contract

Return task-specific fields from `references/schemas.json#/definitions/output`, a fictional worked example in `examples/worked-example.json`, and proposed actual-output criteria in `references/eval-suite.json`. No performance or task qualification is claimed. No runtime JSON state, task ledgers or telemetry; native session is the continuity surface.
