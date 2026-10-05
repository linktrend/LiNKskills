# Source provenance and license disposition

Primary recommendation: Use Anthropic’s question-first visualization guidance for general charts and bring in the trading-specific branch only for trading metrics. Prefer the simplest native chart that preserves comparison and uncertainty.

## Reviewed entrypoints

- Role: **complementary**; repository: `agiprolabs/claude-trading-skills`; path: `skills/trading-visualization/SKILL.md`; commit: `981e1d736cdc02bdc1c55c74ec9224e956414706`; SHA-256: `c04ec0823c9526838cb2f1fff12d87cd08edc636ef47af2451d9ea93317982d8`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **MIT**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Time series/distribution chart forms only; reject forced dark palette and normal-fit/VaR inference as generic defaults.
  - Defect/repair: Do not invent chart data, axes, performance, statistical meaning, or interactive features.; Do not imply a chart proves causation or investment returns; label source and as-of date.
- Role: **complementary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/build-dashboard/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `6f23faa0b266820a23096f76df9d83e6b67597af4fc8c3306b4eba7e9f409f99`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Clarify dashboard audience/metrics/filters and layout; dashboard/CDN/sample-data defaults are optional and not Jane requirements.
  - Defect/repair: Do not invent chart data, axes, performance, statistical meaning, or interactive features.; Do not imply a chart proves causation or investment returns; label source and as-of date.
- Role: **complementary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/create-viz/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `3b13a9c2c9d2b1d36f9c323d952d93f578216f2094bc80d4be6fd4ccbfe9b77d`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Select chart from data relationship; label uncertainty, axis, units and source.
  - Defect/repair: Do not invent chart data, axes, performance, statistical meaning, or interactive features.; Do not imply a chart proves causation or investment returns; label source and as-of date.
- Role: **primary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/data-visualization/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `5811e8b3547cda6bc8af118aaf0d7589e8861cdc9facce6372dc78aea99ab87d`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: data visualization matched to question with accurate scales, units, source and accessibility. Source path contribution: primary branch at data/skills/data-visualization/SKILL.md.
  - Defect/repair: Do not invent chart data, axes, performance, statistical meaning, or interactive features.; Do not imply a chart proves causation or investment returns; label source and as-of date.

## Support closure status

Every direct linked support has a defensible disposition. The listed method-critical references were personally read; remaining scripts/assets/references are inventory-only and not adopted. This is not source-code, live API, legal/clinical currentness, or license admission.

- Direct linked supports: 5; personally read method-critical supports: 0; inventory-only/not adopted: 5.
- Scripts executed: **No**. Scripts and assets not adopted remain inventory-only data; no upstream script or generator was run.
- Any future adaptation needs exact notice preservation, source/code review, and any license disposition required before release. No release/license admission is implied here.

- Notice recorded by audit: `agiprolabs/claude-trading-skills` — `MIT` — Preserve the repository copyright/license notice if source text or code is adapted.
- Notice recorded by audit: `anthropics/knowledge-work-plugins` — `Apache-2.0` — Preserve the repository copyright/license notice if source text or code is adapted.

## Exact-copy manifest

`references/upstream-copy-manifest.json` records every retained entrypoint/support file and copied root license/notice file with source repository, pinned checkout commit, original path, copy path, byte count, and SHA-256. The original audit SHA is cross-checked for every entrypoint. Source copies remain inert provenance data, excluded from routing and execution.
