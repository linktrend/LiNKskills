# Source map and licensing record

Task group 26; trading-defi-liquidity-yield. Source entries below identify the pinned evidence reviewed for this draft. Draft methods are independently written; source inclusion does not qualify the skill.

## skills/dex-pool-analysis/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `44c65cfdc903434f9015e718ca554ca7e9702a7525875401bd0ba363fde90934` (? bytes)
- Contribution considered: Compare pool mechanics and pool state provenance across constant-product, concentrated-liquidity and bin-based designs; distinguish TVL from active depth and record route-specific quote scope.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/impermanent-loss/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `140149abdc5dc64cf6b2e842757a977e0e220b3727c2153aa69567117fbd99a9` (? bytes)
- Contribution considered: Compute LP-versus-hold value under the same relative price path; explain fee-offset break-even and range-specific exposure without treating the closed-form CPMM formula as a CLMM result.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/liquidity-analysis/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `f13ef38efce8206a212e0f657644aa991f4b4643c23dee9fa73cfdc308cfd334` (? bytes)
- Contribution considered: Assess size-dependent depth with reserve math or timestamped quote ladders; separate curve impact, pool fee, aggregator route and execution uncertainty.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/lp-math/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `dabe3bc9ef02221c73db258cf159967e16b9a1d549172d96e0e6f1cc5cfbccd3` (? bytes)
- Contribution considered: Derive reserve/invariant and position-value equations with explicit token orientation, units, fee treatment and starting inventory.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## skills/yield-analysis/SKILL.md
- Repository/commit: `agiprolabs/claude-trading-skills` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`
- Entrypoint SHA-256: `79e3756b74bd02f529f18b548080c09c3a76dae9ef9dd8f0ed28863d91fe45d7` (? bytes)
- Contribution considered: Decompose gross fees, LP fee share, incentives, costs, price-path loss and reinvestment assumptions; test reward sustainability and break-even rather than rank nominal APR.
- Root license evidence: `LICENSE.md` SHA-256 `41c5c4c5e8df2b67fb1d3dc288fad6cb584fab7b50333546d29e8dc6ae941408`; NOTICE `None` SHA-256 `None`; root tracked license verified.
- Disposition: Read-only source evidence; adapt independently. No upstream code executed, no provider/credential use, no install or publication.

## Selected support closure

{"selected_method_critical_paths": ["agiprolabs/claude-trading-skills:skills/dex-pool-analysis/references/pool_mechanics.md", "agiprolabs/claude-trading-skills:skills/dex-pool-analysis/references/pool_analysis_guide.md", "agiprolabs/claude-trading-skills:skills/impermanent-loss/references/il_formulas.md", "agiprolabs/claude-trading-skills:skills/impermanent-loss/references/breakeven_analysis.md", "agiprolabs/claude-trading-skills:skills/liquidity-analysis/references/slippage_curves.md", "agiprolabs/claude-trading-skills:skills/liquidity-analysis/references/pool_types.md", "agiprolabs/claude-trading-skills:skills/lp-math/references/amm_formulas.md", "agiprolabs/claude-trading-skills:skills/yield-analysis/references/yield_math.md", "agiprolabs/claude-trading-skills:skills/yield-analysis/references/sustainability_analysis.md"], "presence": "Selected listed support files exist in pinned checkout; entrypoints and cited method supports read.", "required_vs_optional": "Only the above task-selected calculation/settlement supports are method-critical. Unrelated pool skill assets, scripts, tests and broad repository files are optional inventory, not closure requirements.", "remaining_gap": "No authoritative current pool/router API or on-chain observation proof; no current numeric market conclusion can be claimed."}
All source scripts and live quote/API examples quarantined and unexecuted.
Source audit only; no skill admission/publication.

No upstream scripts, tests, API clients, providers, credentials, adapters, orders or live controls were executed or accessed. Missing support outside this selected task closure is not treated as a release blocker unless the method actually depends on it.

## Exact retained entrypoint captures

Each distinct assigned path is copied byte-for-byte as `SKILL.source.md` under `source-material/upstream/<repo>/<original-directory>/`; one exact root LICENSE and applicable NOTICE accompany that repository. See `references/upstream-copy-manifest.json` for source/copy/license/NOTICE SHA-256 values. No GPL/no-grant source is included.
