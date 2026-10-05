---
name: trading-value-dividend-strategy
description: "Evaluate value, current income, dividend growth, pullback and dividend-policy risk under the user’s stated objective."
usage_trigger: "Use for value/dividend screening, income sustainability, dividend growth during pullbacks, Kanchi-style underwriting, or dividend-risk monitoring."
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
scope_out: ["Do not place orders, contact a broker, alter a portfolio, or activate live capital.", "Do not invent market data, source access, paid entitlements, historical validation, or method passes.", "Do not treat structural validation or fictional fixtures as strategy validation.", "Do not replace the existing LiNKtrading engine or create runtime JSON state/sidecars."]
format_profile: simple
last_updated: 2026-10-05
---

# Value and dividend research

**Status:** Isolated draft v0.1.0. Not admitted, published, selected, activated, or method-qualified. Upstream bytes are preserved as data-only evidence in the external archive described by `references/source-packaging.md` and mapped by `references/source-provenance.json`; they are not active skills.

## Preconditions and native host

Use only when the requested task matches this skill and the required dated inputs are present or can be read from an actually exposed, authorized host capability. Logical `read_file`, `write_file`, and schema-validation labels do not imply those named tools exist: use the host's native persistent-session read/write capability and supplied inline schemas. Do not claim `get_tool_details`, provider, API, CLI or MCP access unless exposed. Tool-routing order is native CLI only if the host exposes and authorizes one; CLI wrapper only if the host exposes it; direct API only if actually authorized; MCP only if an exposed persistent service supports the task. These capability labels do not grant tools or entitlements. Preserve continuity in the one persistent native session; no runtime JSON/JSONL state, sidecar ledger, telemetry rows, provider calls, or external writes are created by this draft.

## Inputs and output contract

Canonical input is `references/schemas.json#/definitions/input`; canonical task-shaped output is `#/definitions/output`. Treat the fictional worked example as a format illustration only. Record supplied facts with source IDs, publication/release time, retrieval/as-of time, unit, period, basis, and transformation. If a required input is absent, return `insufficient_input` or `partial`, identify the exact missing field, and do only independent work that remains valid. Unknown stays null/unknown; never backfill from memory.

## Practical method

1. Identify objective (cash income, dividend growth/total return, or valuation), instrument type, universe, horizon/as-of and user-supplied risk constraints.
2. For each dividend, retain raw payment history with declared date, ex/pay date, cadence, regular/special status and currency; compute regular forward yield separately from TTM/special-inclusive yield, showing formula and price timestamp.
3. Assess growth history, cuts/freezes/variable policy and payout on appropriate denominators: stock FCF, REIT FFO/AFFO, BDC NII; for regulated utilities and banks/insurers use sector evidence, not generic FCF payout.
4. Reconcile GAAP and adjusted earnings, one-off effects, debt/interest coverage and capital return; missing adjusted or sector-critical inputs become review-required/partial, not silently clean.
5. Select valuation by instrument/sector (e.g. bank P/TBV, REIT P/FFO/AFFO, cash-cow P/FCF) and show own-history/peer comparability and ranges; do not apply source P/E×P/B as universal gate.
6. Separate backward earnings one-offs from forward structural events; log source tier, publication/retrieval times, URL/file and event scan window. Missing/unavailable scan on a triggered item remains unresolved/review-required.
7. If requested, calculate pullback triggers from stated yield/valuation history and show hypothetical price/valuation assumptions, invalidation and downside. Jane may recommend conditional strategy/sizing/exit only with holdings, liquidity and risk constraints supplied.
8. Return objective-specific candidate table/memo/monitor queue, explicit missing evidence and conditional conclusion. No tax/account-location determinations, order submission, auto-add/auto-sell, live portfolio mutation or capital activation.

## Source-specific branches

- **tradermonty/claude-trading-skills — `skills/value-dividend-screener/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Keep yield/valuation filters as candidate generation only; verify regular versus special and use sector-appropriate coverage.
- **dr-pabs/Agent-claude-trading-skills — `skills/dividend-growth-pullback-screener/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Treat dividend growth history and RSI pullback as separate observations; no reversal probability or automatic entry.
- **dr-pabs/Agent-claude-trading-skills — `skills/kanchi-dividend-review-monitor/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Use risk triggers to produce review/warn queue only; no automatic sell/add.
- **dr-pabs/Agent-claude-trading-skills — `skills/kanchi-dividend-sop/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Select user objective; retain latest source’s regular-forward yield, sector dispatch, evidence provenance and forward-event scan; older threshold/entry variants stay separate.
- **dr-pabs/Agent-claude-trading-skills — `skills/value-dividend-screener/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Keep yield/valuation filters as candidate generation only; verify regular versus special and use sector-appropriate coverage.
- **mphinance/alpha-skills — `skills/dividend-growth-pullback-screener/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Treat dividend growth history and RSI pullback as separate observations; no reversal probability or automatic entry.
- **mphinance/alpha-skills — `skills/kanchi-dividend-review-monitor/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Use risk triggers to produce review/warn queue only; no automatic sell/add.
- **mphinance/alpha-skills — `skills/kanchi-dividend-sop/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Select user objective; retain latest source’s regular-forward yield, sector dispatch, evidence provenance and forward-event scan; older threshold/entry variants stay separate.
- **mphinance/alpha-skills — `skills/value-dividend-screener/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Keep yield/valuation filters as candidate generation only; verify regular versus special and use sector-appropriate coverage.
- **tradermonty/claude-trading-skills — `skills/dividend-growth-pullback-screener/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Treat dividend growth history and RSI pullback as separate observations; no reversal probability or automatic entry.
- **tradermonty/claude-trading-skills — `skills/kanchi-dividend-review-monitor/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Use risk triggers to produce review/warn queue only; no automatic sell/add.
- **tradermonty/claude-trading-skills — `skills/kanchi-dividend-sop/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Select user objective; retain latest source’s regular-forward yield, sector dispatch, evidence provenance and forward-event scan; older threshold/entry variants stay separate.

## Failure handling and boundaries

- Missing/stale/conflicting data: stop dependent calculations, preserve observed values, mark partial/no-view and name the next evidence needed.
- Conflicting strategy variants: select by the user’s stated objective; do not average thresholds or silently switch strategy.
- Jane may give conditional research/strategy/position-sizing/exit recommendations when requested and supplied constraints support them. Recommendations are advice only and never authorize external action.
- No manual trading, order placement, broker interaction, portfolio mutation or live activation. Any later activation remains on LiNKtrading and requires Lisa plus Carlos independent authenticated approvals over two channels against the exact version.
- Eric owns software/Nautilus adapters; Sara owns legal/accounting determinations.

## Source provenance and licensing

`references/source-provenance.json` indexes exact source hashes, commits, paths, notices, copies and excluded/unread supports. Quarantine notice states permitted copying basis and modifications. Upstream source scripts were not executed or copied. Source statements do not certify method performance or current API availability.

## Proposed evaluation

`references/eval-suite.json` contains proposed output criteria and adversarial cases only. No behavior evaluation ran. The helper checks supplied JSON shape only and must never manufacture a behavioral PASS.

## References

- `references/schemas.json` — concrete input/output structures.
- `examples/worked-example.json` — fictional task-shaped input/output.
- `references/source-provenance.json` and ``references/source-provenance.json` and `references/source-packaging.md` — data-only source index and quarantine rules; no raw upstream README is routed as a method.` — source index/quarantine.
- `references/eval-suite.json` — proposed actual-output criteria, not executed.
- `references/old-patterns.md`, `references/changelog.md`, `advanced/advanced.md`, `scripts/helper_tool.py` — draft maintenance/structure.
