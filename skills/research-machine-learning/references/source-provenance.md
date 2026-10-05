# Source provenance and license disposition

Primary recommendation: Use scikit-learn’s pipeline/evaluation concepts as the primary general method and aeon as a focused time-series branch. Keep forecasting ensemble methods optional and require a deployment-matched holdout.

## Reviewed entrypoints

- Role: **complementary**; repository: `K-Dense-AI/scientific-agent-skills`; path: `skills/aeon/SKILL.md`; commit: `154988403bb5a18e9d3c0ce4e6d5e2e4b184a298`; SHA-256: `e1d25cbe0ba5f849299e9e02bd339773bb41529dcece5a6ee68bb080855b97a6`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **MIT**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Specialized time-series estimators with capability/shape constraints, simple baselines, and temporal/group validation.
  - Defect/repair: Do not use random train/test splits for temporal forecasting or repeated entities without justification.; Prevent target leakage and preprocessing leakage; tuning must not consume the final holdout.
- Role: **primary**; repository: `K-Dense-AI/scientific-agent-skills`; path: `skills/scikit-learn/SKILL.md`; commit: `154988403bb5a18e9d3c0ce4e6d5e2e4b184a298`; SHA-256: `a1765797d072ab40094522abe68fb04505d0881f66b7dfceeb8582422dbe488d`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **MIT**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Preprocessing pipelines prevent leakage; grouped and temporal splits must match deployment, with a final holdout protected from tuning.
  - Defect/repair: Do not use random train/test splits for temporal forecasting or repeated entities without justification.; Prevent target leakage and preprocessing leakage; tuning must not consume the final holdout.
- Role: **complementary**; repository: `ml4t/skills`; path: `advanced-ai/multi-agent-forecasting/SKILL.md`; commit: `f0ea01919e0c517cd9b1e014724a520facd8a742`; SHA-256: `d942cf57d4fe38ff0fc765ce862aaca5d37cb8843fe7df54cee9b265f26b9bb3`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Forecast aggregation needs structural diversity, resolved-question proper scores and ablations; correlated-agent consensus or heuristic diversity multipliers do not establish accuracy.
  - Defect/repair: Do not use random train/test splits for temporal forecasting or repeated entities without justification.; Prevent target leakage and preprocessing leakage; tuning must not consume the final holdout.

## Support closure status

Every direct linked support has a defensible disposition. The listed method-critical references were personally read; remaining scripts/assets/references are inventory-only and not adopted. This is not source-code, live API, legal/clinical currentness, or license admission.

- Direct linked supports: 19; personally read method-critical supports: 0; inventory-only/not adopted: 19.
- Scripts executed: **No**. Scripts and assets not adopted remain inventory-only data; no upstream script or generator was run.
- Any future adaptation needs exact notice preservation, source/code review, and any license disposition required before release. No release/license admission is implied here.

- Notice recorded by audit: `K-Dense-AI/scientific-agent-skills` — `MIT` — Preserve the repository copyright/license notice if source text or code is adapted.
- Notice recorded by audit: `ml4t/skills` — `Apache-2.0` — Preserve the repository copyright/license notice if source text or code is adapted.

## Exact-copy manifest

`references/upstream-copy-manifest.json` records every retained entrypoint/support file and copied root license/notice file with source repository, pinned checkout commit, original path, copy path, byte count, and SHA-256. The original audit SHA is cross-checked for every entrypoint. Source copies remain inert provenance data, excluded from routing and execution.
