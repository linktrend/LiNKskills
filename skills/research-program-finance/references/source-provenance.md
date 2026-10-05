# Source provenance and license disposition

## Audited entrypoint

- Repository: `alirezarezvani/claude-skills`
- Source: `research-ops/skills/research-finance/SKILL.md`
- Commit: `19392f7a08264ed00486a251f5b2098321771f94`
- SHA-256: `a40e86d877bcab0a8c9018dca2b63e69fe1b2d9cf3d41c0f852abda699794ff4`
- Audit status: complete entrypoint read; useful boundary is R&D program budget/cash/milestone evidence, not accounting judgment.
- License recorded in source audit: **MIT**. Preserve the repository copyright/license notice if any source text or code is later adapted. The active method is independently authored. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.

## Method-critical support read for this draft

These files were read directly before writing this package. Their legal/accounting assertions and numerical defaults were not adopted as rules; current controlling source documents must be confirmed by Sara/controller for each award and jurisdiction.

- `research-ops/skills/research-finance/references/rd_program_finance_canon.md`: the program-budget/direct-vs-indirect framing and need to identify applicable framework; any stated legal/accounting treatment and rate figures are not copied or treated as current authority.
- `research-ops/skills/research-finance/references/burn_and_portfolio.md`: cash burn and runway should align by period to milestones; do not carry its fixed acceleration ratio, Stage-Gate decision model, risk-adjusted valuation, or portfolio benchmarks into this coordination skill.
- `research-ops/skills/research-finance/references/indirect_rate_modeling.md`: the rate depends on its specified base, exclusions, and source; do not reuse its default percentages, dollar thresholds, or category eligibility as a universal rule.
- `research-ops/skills/research-finance/assets/rd_program_budget_template.md`: read for task-critical fields (periods, work packages, actuals/forecast, restrictions, F&A basis, milestones, owner). Template values/categories are not adopted as accounting guidance.

## Not adopted

- `research-ops/skills/research-finance/scripts/program_budget_planner.py`
- `research-ops/skills/research-finance/scripts/burn_runway_tracker.py`
- `research-ops/skills/research-finance/scripts/capex_vs_opex_router.py`
- `research-ops/skills/research-finance/scripts/ar_evaluator.py`
- None was copied or executed. They remain inventory-only data and require direct code/math/API review plus owner and license review before any future use.

## Target correction and qualification

The original task-group action was labeled `improve_existing_target_missing_hold`; parent review confirmed that no exact canonical `research-program-finance` target exists and the neighboring `finance-accounting-operations` and broad `research` skills have distinct scopes. This package is therefore authored as a **new distinct draft skill**, not a modification of either canonical skill. It remains unqualified, uncertified, and unpublished; support review is not release or accounting admission.

## Exact-copy manifest

`references/upstream-copy-manifest.json` records every retained entrypoint/support file and copied root license/notice file with source repository, pinned checkout commit, original path, copy path, byte count, and SHA-256. The original audit SHA is cross-checked for every entrypoint. Source copies remain inert provenance data, excluded from routing and execution.
