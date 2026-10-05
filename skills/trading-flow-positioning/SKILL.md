---
name: trading-flow-positioning
description: Analyze dated, supplied institutional 13F ownership or CFTC legacy COT positioning; quantify changes with coverage and reporting lag, and explain their limited evidentiary meaning.
usage_trigger: Institutional ownership changes, a named manager's disclosed filing, COT positioning, or crowding context.
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
scope_out: ["No paid API assumptions, credential retrieval, orders, or live portfolio effects.", "No treating lagged holdings or positioning as a real-time signal or causal explanation.", "No conflating 13F, COT, and fund-flow datasets.", "No fabricated data, manager identities, filings, or vendor entitlements."]
format_profile: simple
last_updated: 2026-10-05
---

# Dated positioning research

**Status:** isolated draft; not admitted, published, activated, or method-certified. Jane may provide conditional research conclusions and recommendations when requested and supported by supplied data. Orders and live effects are outside this skill.

## Host capability mapping

Frontmatter `read_file` and `write_file` are portable logical aliases for the host's native persistent-session read/write capability, not promises that tools with those names exist. Use the supplied inline schemas for schema discovery. Do not invoke `read_file` or `write_file` by name unless those exact tools are exposed. Call `get_tool_details` only if the host actually exposes it and additional detail is needed.


Portable manifest `read_file` and `write_file` labels mean the host's native persistent-session read/write capability; validate against supplied inline schemas. Do not assume named host tools, a native CLI, CLI wrapper, direct API, MCP, or paid vendor connection exists; use those routes only if actually exposed and authorized. Use only a user-supplied dataset or an actually exposed, authorized read-only source. Eric owns adapters for the existing LiNKtrading engine.

## Inputs and source branches

Use `references/schemas.json#/definitions/input` and `#/definitions/output`. Select exactly one `source_family` (`13f` or `cot_legacy`) per calculation. `family_data_status` distinguishes `provided`, `not_supplied`, and `unavailable`. Holdings and COT rows are optional input fields; include only the selected family's rows when supplied. If missing or inaccessible, return `insufficient_input` or `partial`, an explicit unknown family result, and the exact missing field. Never require an empty placeholder array for the other family.

- **13F holdings:** supplied filing rows with manager/security identifiers, shares, report-period end, filing/publication date, and source. Use share changes for position change. Report disclosed long holdings only; 13F does not reveal shorts, intraperiod changes, or current positions. Distinguish new/exited from unavailable matching rows.
- **CFTC legacy COT:** supplied weekly report rows with report date, publication date, contract identity, non-commercial long/short, and open interest. Net position = non-commercial long minus short. The lookback index is `(current_net - window_min)/(window_max - window_min)*100`; return unknown when the history is short or range is zero. 156-week index is primary and 26-week index context only if enough supplied history exists. State the selected vintage and thresholds; extremes flag positioning only, never a trade signal.
- Public fund-flow series are not admitted: require an identified dataset, share/flow definition, timing, and source contract before analysis.

## Method

1. Verify issuer/contract identity, report family, unit, dates, publication lag, row coverage, and correction/republication handling from supplied evidence.
2. Compare only like periods and matching identifiers. For 13F, calculate shares added/removed and concentration only when denominator and comparable holder coverage are supplied. Market-value change is not share-flow change.
3. For COT, sort weekly rows by report date; document duplicate-date choice, history length, net positions, open-interest denominator, and zero/invalid denominator. Never mix legacy non-commercial fields with disaggregated categories.
4. Present observations and calculations before interpretation. Discuss concentration, breadth, and lag; do not infer intent, short positions, causation, or forward returns from holdings alone.
5. Give a conditional advisory takeaway only if requested. State counterevidence and what new filing/report would change it. Validate the actual output shape; schema validity does not qualify the method.

## Outputs

Return either a 13F ownership-change memo or COT crowding context table as defined by the schema. Preserve source rows, dates, units, coverage, and unknowns. Do not create runtime JSON state, task ledgers, or telemetry sidecars; persistent native session state carries continuity.

## Source variants and limits

`references/source-provenance.json` indexes exact pinned entrypoints and selected method supports. The two 13F branches disagree on reliability-grade inputs and holder filtering; do not merge their grades. Omit numerical conviction grades. The COT branch contributes a bounded lagged crowding calculation; news failure and chart confirmation are separate evidence requests and never synthesized.

## References

- `references/schemas.json`: two task-shaped input/output variants.
- `references/source-provenance.json`: source hashes, license files, and closure limits.
- `references/eval-suite.json`: proposed actual-output review criteria; none run.
- `examples/worked-example.json`: fictional 13F sample; no investment result.
- `examples/source-variants.json`: fictional COT math example and 13F/COT distinction.
- `references/upstream/`: data-only quarantine; not skill instructions or executable code.
