# Source map and licensing record

Task group 27; trading-prediction-market-strategy. Source entries below identify the pinned evidence reviewed for this draft. Draft methods are independently written; source inclusion does not qualify the skill.

## skills/llmquant-prediction-markets/SKILL.md
- Repository/commit: `LLMQuant/skills` @ `1918237467c2dff4cc97a18ebc0892dfd46e8129`
- Entrypoint SHA-256: `2f3c0623b84e9973999e42d5495052265e37aa9c1e6e3a52033b3a27c321a9d9` (? bytes)
- Contribution considered: Build a contract-specific probability brief and compare model probability with executable bid/ask after fees only when settlement, timestamp, depth and expiry align.
- Root license evidence: `LICENSE` SHA-256 `62653711a0212fce2fced9e92dbf4ccea3e1d3aacd51678b9478551b8dc15e7b`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/kalshi-crypto-index-markets/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `822a1967bd3e0f622750593a0548723c8edb7f71864f4c38964b4dd209108e1f` (? bytes)
- Contribution considered: Decode the exact index/series/threshold settlement rule and model a distribution only with timestamped inputs and declared horizon; unresolved contract rule blocks numerical probability.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/kalshi-weather-markets/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `c641f1719e7543d14ae754ed56e0438351dbf388c8000c431b2191f1680448aa` (? bytes)
- Contribution considered: Map station, observation window, unit, rounding, tie/bracket settlement and forecast distribution to each outcome; keep forecast probability distinct from displayed price.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/prediction-market-live-ops/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `0103677f019de0fc1d8e00cdff78e02dfedf30021956dce90c535befcc01e259` (? bytes)
- Contribution considered: Inventory operational/live-order procedures for quarantine and hazard detection only; do not import account, deployment, signing, order or automation steps into Jane task.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/prediction-market-strategy/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `03cc9b80ac4a6f1e89bbfde484b9025ad7e9ddb6f46c4758f2fbe859bcca6b47` (? bytes)
- Contribution considered: Compare event probability to contract price, payoff, fees, liquidity and dependence; classify apparent arbitrage only after exhaustive mutually exclusive settlement and capital paths are verified.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## Selected support closure

{"selected_method_critical_paths": ["LLMQuant/skills:skills/llmquant-prediction-markets/workflows/event-probability-brief.md", "LLMQuant/skills:skills/llmquant-prediction-markets/workflows/prediction-market-arb-watch.md", "LLMQuant/skills:skills/llmquant-prediction-markets/workflows/probability-vs-options-pricing.md", "agiprolabs/claude-trading-skills:skills/kalshi-crypto-index-markets/references/structure-and-modeling.md", "agiprolabs/claude-trading-skills:skills/kalshi-weather-markets/references/brackets-and-settlement.md", "agiprolabs/claude-trading-skills:skills/kalshi-weather-markets/references/forecasting.md", "agiprolabs/claude-trading-skills:skills/prediction-market-strategy/references/sizing-and-edge-gates.md", "agiprolabs/claude-trading-skills:skills/prediction-market-strategy/references/backtesting-methodology.md", "agiprolabs/claude-trading-skills:skills/prediction-market-strategy/references/strategy-catalog.md", "agiprolabs/claude-trading-skills:skills/prediction-market-strategy/references/evidence-and-literature.md"], "presence": "Selected workflow and settlement/sizing/backtest references read and present.", "required_vs_optional": "Only contract/settlement, probability framing, sizing, and historical-evaluation supports listed here are critical. Other event/market workflows are optional.", "remaining_gap": "Crypto/index settlement branch has unresolved missing target `agiprolabs/claude-trading-skills:skills/prediction-markets/references/brackets-and-settlement.md`; exact market rulebook and current fees/depth/settlement contract must be user-supplied or separately verified by an authorized research path."}
No source scripts or venue/API operations run; live-ops entrypoint quarantined.
Research and advisory only; no contract/API qualification.

No upstream scripts, tests, API clients, providers, credentials, adapters, orders or live controls were executed or accessed. Missing support outside this selected task closure is not treated as a release blocker unless the method actually depends on it.

## Exact retained entrypoint captures

Each distinct assigned path is copied byte-for-byte as `SKILL.source.md` under `source-material/upstream/<repo>/<original-directory>/`; one exact root LICENSE and applicable NOTICE accompany that repository. See `references/upstream-copy-manifest.json` for source/copy/license/NOTICE SHA-256 values. No GPL/no-grant source is included.
