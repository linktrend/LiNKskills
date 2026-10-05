# Source map and licensing record

Task group 29; trading-microstructure-execution-analysis. Source entries below identify the pinned evidence reviewed for this draft. Draft methods are independently written; source inclusion does not qualify the skill.

## skills/market-microstructure-traditional/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `0164b87caa8b2f8ce1554d7ba47e68d7d8ac417f43238cc3eced106707e74a1e` (? bytes)
- Contribution considered: Evaluate historical spread, depth, order imbalance, Kyle impact and execution shortfall with explicit signed side, horizon, sampling interval and notional/price units.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/market-microstructure/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `65d5b86cdf96f67994f77316b7aac67f4b42d72e1907b47e1af181eb82d290e9` (? bytes)
- Contribution considered: Interpret supplied DEX/CEX trade prints and order-flow proxies; retain confidence limits, remove duplicate route legs and treat wallet/flow indicators as evidence rather than intent.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/mev-analysis/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `48f45e49c39b20da484483a0b77a310da93a064c444985d6b9a90985d64933e4` (? bytes)
- Contribution considered: Assess historical transaction exposure and user cost from supplied public evidence; no transaction construction, signing, submission, RPC/provider or protection activation.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/rl-execution/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `24a729f221aaaf5eb07100d680973b6eb497d9aa1a92d8456c0e3194382fb640` (? bytes)
- Contribution considered: Use TWAP/VWAP/Almgren-Chriss and RL state/reward concepts to explain backtest assumptions and model gaps; no policy training, software or live order authority.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## backtest/rl-execution/SKILL.md
- Repository/commit: `ml4t/skills` @ `f0ea01919e0c517cd9b1e014724a520facd8a742`
- Entrypoint SHA-256: `c3920babfac6f2ed718615f8a6505e7e41c450dbcc1324633d3cbe99e5e5b9ab` (? bytes)
- Contribution considered: Use TWAP/VWAP/Almgren-Chriss and RL state/reward concepts to explain backtest assumptions and model gaps; no policy training, software or live order authority.
- Root license evidence: `LICENSE` SHA-256 `e97825a2b0db1501085feecd0a5f5237483dee279263171e387632a361590c5c`; NOTICE `NOTICE` SHA-256 `a8f05028aa76c237784df8b02b0a10a468430d191b802da052348a62d2855f5b`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## Selected support closure

{"selected_method_critical_paths": ["agiprolabs/claude-trading-skills:skills/market-microstructure-traditional/references/price_formation.md", "agiprolabs/claude-trading-skills:skills/market-microstructure-traditional/references/execution_quality.md", "agiprolabs/claude-trading-skills:skills/market-microstructure-traditional/references/cex_vs_dex.md", "agiprolabs/claude-trading-skills:skills/market-microstructure/references/trade_classification.md", "agiprolabs/claude-trading-skills:skills/market-microstructure/references/flow_signals.md", "agiprolabs/claude-trading-skills:skills/market-microstructure/references/wash_trading.md", "agiprolabs/claude-trading-skills:skills/mev-analysis/references/solana_mev_mechanics.md", "agiprolabs/claude-trading-skills:skills/mev-analysis/references/protection_strategies.md", "agiprolabs/claude-trading-skills:skills/rl-execution/references/execution_algorithms.md", "agiprolabs/claude-trading-skills:skills/rl-execution/references/rl_framework.md"], "presence": "Listed market, execution, MEV and RL method references checked in pinned source.", "required_vs_optional": "These selected methods support the task branches. Broker/RPC/vendor integration references, scripts, training frameworks and unused assets remain optional/quarantined, not missing dependencies.", "remaining_gap": "No current venue/chain/exchange contract was needed or verified because task is historical evidence analysis; if a future task depends on live market/provider behavior, Eric must validate exact enabled integration contracts before adoption."}
No MEV/RL/adapter script executed; quoted live/provider/transaction paths quarantined.
Forensic/advisory method draft only.

No upstream scripts, tests, API clients, providers, credentials, adapters, orders or live controls were executed or accessed. Missing support outside this selected task closure is not treated as a release blocker unless the method actually depends on it.

## Exact retained entrypoint captures

Each distinct assigned path is copied byte-for-byte as `SKILL.source.md` under `source-material/upstream/<repo>/<original-directory>/`; one exact root LICENSE and applicable NOTICE accompany that repository. See `references/upstream-copy-manifest.json` for source/copy/license/NOTICE SHA-256 values. No GPL/no-grant source is included.
