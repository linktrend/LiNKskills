# Source map and licensing record

Task group 37; trading-portfolio-exposure-risk. Source entries below identify the pinned evidence reviewed for this draft. Draft methods are independently written; source inclusion does not qualify the skill.

## skills/llmquant-portfolio/SKILL.md
- Repository/commit: `LLMQuant/skills` @ `1918237467c2dff4cc97a18ebc0892dfd46e8129`
- Entrypoint SHA-256: `8bfd0a2b3de6a7867d786c04531436f9d12a1ea3e5171205334d347044bad591` (? bytes)
- Contribution considered: Use the portfolio exposure-map and what-if workflows to organize holdings, concentration, correlations and scenario deltas from user-supplied snapshot; no account calls.
- Root license evidence: `LICENSE` SHA-256 `62653711a0212fce2fced9e92dbf4ccea3e1d3aacd51678b9478551b8dc15e7b`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/llmquant-risk/SKILL.md
- Repository/commit: `LLMQuant/skills` @ `1918237467c2dff4cc97a18ebc0892dfd46e8129`
- Entrypoint SHA-256: `8b36e01b21acd8021813f534861af62d40a96bdf232bf87ca879fd1df6e1491c` (? bytes)
- Contribution considered: Use risk workflows to label specified stress/drawdown exposures and compare against owner-provided limits; treat thresholds as configurable hypotheses, never policy defaults.
- Root license evidence: `LICENSE` SHA-256 `62653711a0212fce2fced9e92dbf4ccea3e1d3aacd51678b9478551b8dc15e7b`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/correlation-analysis/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `035bba5b31dbe756447b6620059dcc35a66105cc91727db98fa9cd9469098b93` (? bytes)
- Contribution considered: Estimate return dependence with aligned dates/frequency, rolling and lower-tail views, confidence limits and covariance diagnostics; translate to portfolio risk contribution only after weights supplied.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/risk-management/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `cc7c016d080bed83eb5cca2e23d9d0ab767ea9abd215a77c51d86494c2438ec5` (? bytes)
- Contribution considered: Structure scenario, drawdown, exposure and escalation analysis; historical hard limits/circuit breakers are examples, not authority or installed rules.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/exposure-coach/SKILL.md
- Repository/commit: `dr-pabs/Agent-claude-trading-skills` @ `4ff3f81c176e46449e388d15676643d4b714a3da`
- Entrypoint SHA-256: `434c4c7e89010eca9ac1ad75f57091b8b865ecdabb2cfa241a9fc70603cd7d9b` (? bytes)
- Contribution considered: Combine explicitly provided regime/breadth/flow evidence into a transparent exposure posture; missing/conflicting components lower confidence and cannot set ceilings autonomously.
- Root license evidence: `LICENSE` SHA-256 `87c93cde8c3a000c19b0c790cd4f7a4e4cb8da5bc6b11e0939bf6df99e245d15`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/portfolio-manager/SKILL.md
- Repository/commit: `dr-pabs/Agent-claude-trading-skills` @ `4ff3f81c176e46449e388d15676643d4b714a3da`
- Entrypoint SHA-256: `43ec828602b0b047fe38a76d44fa2d313713603f9770ed368ed0eac343d03797` (? bytes)
- Contribution considered: Use allocation, concentration, drawdown and thesis sections from supplied portfolio snapshot only; quarantine Alpaca MCP/API, market-data calls, scripts, tax/legal, order quantities and live trade flow.
- Root license evidence: `LICENSE` SHA-256 `87c93cde8c3a000c19b0c790cd4f7a4e4cb8da5bc6b11e0939bf6df99e245d15`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## portfolio/exposure-analysis/SKILL.md
- Repository/commit: `ml4t/skills` @ `f0ea01919e0c517cd9b1e014724a520facd8a742`
- Entrypoint SHA-256: `1da5e316eb9f4b61a506be651603a7b1d2dac508ece1112483b72baf381f22d5` (? bytes)
- Contribution considered: Source entrypoint read; capability is inventory-only pending method-specific adoption decision.
- Root license evidence: `LICENSE` SHA-256 `e97825a2b0db1501085feecd0a5f5237483dee279263171e387632a361590c5c`; NOTICE `NOTICE` SHA-256 `a8f05028aa76c237784df8b02b0a10a468430d191b802da052348a62d2855f5b`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## portfolio/risk-metrics/SKILL.md
- Repository/commit: `ml4t/skills` @ `f0ea01919e0c517cd9b1e014724a520facd8a742`
- Entrypoint SHA-256: `6b1840c03b12962790f162434af701ea0178e6d093da9575c2d7d3e46aac2ca1` (? bytes)
- Contribution considered: Source entrypoint read; capability is inventory-only pending method-specific adoption decision.
- Root license evidence: `LICENSE` SHA-256 `e97825a2b0db1501085feecd0a5f5237483dee279263171e387632a361590c5c`; NOTICE `NOTICE` SHA-256 `a8f05028aa76c237784df8b02b0a10a468430d191b802da052348a62d2855f5b`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/exposure-coach/SKILL.md
- Repository/commit: `mphinance/alpha-skills` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`
- Entrypoint SHA-256: `de5dcc1bad1b25c061207c762b71720eadf844b417a54ab508e064c9f1a5ce1c` (? bytes)
- Contribution considered: Synthesize sourced component measures into conditional posture, preserving missingness; its static scoring and decision categories are hypotheses only.
- Root license evidence: `LICENSE` SHA-256 `96905efb08aad62c0a7f950d3a327cb77d131a69af974362252525e2e585d3cc`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/portfolio-manager/SKILL.md
- Repository/commit: `mphinance/alpha-skills` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`
- Entrypoint SHA-256: `a079516e4f901839cf8d562ca1ff455002b0a4be1c5d3915f3a7d4f6baea44ea` (? bytes)
- Contribution considered: Use portfolio reporting structure and scenario/rebalance comparison for supplied holdings; external broker/data calls and transaction-ready recommendations are out of scope.
- Root license evidence: `LICENSE` SHA-256 `96905efb08aad62c0a7f950d3a327cb77d131a69af974362252525e2e585d3cc`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/exposure-coach/SKILL.md
- Repository/commit: `tradermonty/claude-trading-skills` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`
- Entrypoint SHA-256: `17cd0765062f1957daaa569b0d5f2138fa90e0728eee7d2b29635e1d3bdfb0c9` (? bytes)
- Contribution considered: Cross-check exposure posture and state component support/conflict; use no fixed ceiling unless user has supplied an applicable limit.
- Root license evidence: `LICENSE` SHA-256 `87c93cde8c3a000c19b0c790cd4f7a4e4cb8da5bc6b11e0939bf6df99e245d15`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/portfolio-manager/SKILL.md
- Repository/commit: `tradermonty/claude-trading-skills` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`
- Entrypoint SHA-256: `2e7c0863ca2cb5510df60d5108486f9686dc3fdac21819f701f766bd28a59265` (? bytes)
- Contribution considered: Use holdings/allocation/risk report structure as a complementary checklist; do not install alternate broker or emit executable orders.
- Root license evidence: `LICENSE` SHA-256 `87c93cde8c3a000c19b0c790cd4f7a4e4cb8da5bc6b11e0939bf6df99e245d15`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## Selected support closure

{"selected_method_critical_paths": ["agiprolabs/claude-trading-skills:skills/correlation-analysis/references/methodology.md", "agiprolabs/claude-trading-skills:skills/correlation-analysis/references/portfolio_applications.md", "agiprolabs/claude-trading-skills:skills/risk-management/references/drawdown_management.md", "agiprolabs/claude-trading-skills:skills/risk-management/references/exposure_limits.md", "agiprolabs/claude-trading-skills:skills/risk-management/references/circuit_breakers.md", "dr-pabs/Agent-claude-trading-skills:skills/exposure-coach/references/exposure_framework.md", "dr-pabs/Agent-claude-trading-skills:skills/exposure-coach/references/regime_exposure_map.md", "ML4T/skills:portfolio/risk-metrics/SKILL.md", "ML4T/skills:portfolio/exposure-analysis/SKILL.md"], "presence": "Selected correlation, risk, exposure, risk metrics and portfolio reference paths exist; ML4T entrypoints are self-contained.", "required_vs_optional": "Only the selected correlation, drawdown, exposure-limit, circuit-breaker and exposure-posture methods above are task-critical and reviewed. Portfolio-manager reference catalogues and any broker connectors, scripts, unrelated portfolio reference files or repo-wide assets are optional or excluded; support-scan repository-wide counts do not create task dependencies.", "remaining_gap": "Current account/market snapshot, factor/benchmark history and user risk limits are task inputs not source dependencies; no current provider contract is needed absent an authorized external data task."}
No score engine, broker API, portfolio writer or risk circuit breaker executed.
Advisory task-method draft; no portfolio policy or live eligibility.

No upstream scripts, tests, API clients, providers, credentials, adapters, orders or live controls were executed or accessed. Missing support outside this selected task closure is not treated as a release blocker unless the method actually depends on it.

## Exact retained entrypoint captures

Each distinct assigned path is copied byte-for-byte as `SKILL.source.md` under `source-material/upstream/<repo>/<original-directory>/`; one exact root LICENSE and applicable NOTICE accompany that repository. See `references/upstream-copy-manifest.json` for source/copy/license/NOTICE SHA-256 values. No GPL/no-grant source is included.
