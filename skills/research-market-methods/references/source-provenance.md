# Source provenance and license disposition

Primary recommendation: Use the ResearchOps method for market boundaries, sizing, survey design, and segment evidence; use the financial-services competitor branch for comparable company analysis. Triangulate where evidence exists and show ranges rather than forced precision.

## Reviewed entrypoints

- Role: **primary**; repository: `alirezarezvani/claude-skills`; path: `research-ops/skills/market-research/SKILL.md`; commit: `19392f7a08264ed00486a251f5b2098321771f94`; SHA-256: `0e4037294f8e6bea1cb53de035eaa97bd2d74349d06f9b61d85f4420d7c084c9`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **MIT**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: market sizing, survey, segmentation and competitive-method evidence. Source path contribution: primary branch at research-ops/skills/market-research/SKILL.md.
  - Defect/repair: Keep primary market research separate from campaign analytics, GTM execution, and pricing decisions.; Top-down/bottom-up are useful triangulation methods, not mandatory if inputs are unavailable; label one-sided estimates and data gaps.
- Role: **complementary**; repository: `anthropics/financial-services`; path: `plugins/agent-plugins/market-researcher/skills/competitive-analysis/SKILL.md`; commit: `574ed3624aebd0418c7e96cd101262f30210ab26`; SHA-256: `65c6e2a68ba67660076e1f5b7d3602f71b3e97d3cdc1f2a6b03c12c05c24f1f9`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Comparable metric periods, citations, consistent definitions and market-context map; investment probabilities and sample figures are not adopted.
  - Defect/repair: Keep primary market research separate from campaign analytics, GTM execution, and pricing decisions.; Top-down/bottom-up are useful triangulation methods, not mandatory if inputs are unavailable; label one-sided estimates and data gaps.

## Support closure status

Every direct linked support has a defensible disposition. The listed method-critical references were personally read; remaining scripts/assets/references are inventory-only and not adopted. This is not source-code, live API, legal/clinical currentness, or license admission.

- Direct linked supports: 10; personally read method-critical supports: 0; inventory-only/not adopted: 10.
- Scripts executed: **No**. Scripts and assets not adopted remain inventory-only data; no upstream script or generator was run.
- Any future adaptation needs exact notice preservation, source/code review, and any license disposition required before release. No release/license admission is implied here.

- Notice recorded by audit: `alirezarezvani/claude-skills` — `MIT` — Preserve the repository copyright/license notice if source text or code is adapted.
- Notice recorded by audit: `anthropics/financial-services` — `Apache-2.0` — Preserve the repository copyright/license notice if source text or code is adapted.

## Exact-copy manifest

`references/upstream-copy-manifest.json` records every retained entrypoint/support file and copied root license/notice file with source repository, pinned checkout commit, original path, copy path, byte count, and SHA-256. The original audit SHA is cross-checked for every entrypoint. Source copies remain inert provenance data, excluded from routing and execution.
