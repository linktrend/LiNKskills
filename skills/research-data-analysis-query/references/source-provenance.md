# Source provenance and license disposition

Primary recommendation: Use the data plugin’s profile→question→query→interpretation sequence and keep context extraction as an explicit branch. This yields traceable analysis without depending on a particular warehouse connector.

## Reviewed entrypoints

- Role: **primary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/analyze/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `4ee816363d944c7a959e43384576d979a414f37fff7071c0bfb8935aae10143e`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: read-only data profiling, SQL drafting and metric analysis within explicitly authorized scope. Source path contribution: primary branch at data/skills/analyze/SKILL.md.
  - Defect/repair: Do not query, export, or modify a database without explicit scope and read/write authorization.; Do not assume internal connectors or schema context exist; ask for access/input only when needed.
- Role: **complementary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/data-context-extractor/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `6d05dec52ac3667b551898b9eb943f5ee08141bc8d2fabb69a8e39bb9ce7c754`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Capture entity/grain/IDs/metric definitions, joins and hygiene from supplied context; no assumed live warehouse access.
  - Defect/repair: Do not query, export, or modify a database without explicit scope and read/write authorization.; Do not assume internal connectors or schema context exist; ask for access/input only when needed.
- Role: **complementary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/explore-data/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `af7590fa616360259da712b5ede5f79b817beb854c47a465f95774354988e8a2`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Profile grain, keys, nulls, cardinality, distributions, dates, duplicates and freshness before analysis.
  - Defect/repair: Do not query, export, or modify a database without explicit scope and read/write authorization.; Do not assume internal connectors or schema context exist; ask for access/input only when needed.
- Role: **complementary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/sql-queries/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `dbd5a5e2d563d83ca6d4d033206f285f503296eabff4a35545cdb4cb5302bd9a`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Use readable dialect-specific query patterns, qualified joins, bounded columns/filters and explicit grain; verify against schema.
  - Defect/repair: Do not query, export, or modify a database without explicit scope and read/write authorization.; Do not assume internal connectors or schema context exist; ask for access/input only when needed.
- Role: **complementary**; repository: `anthropics/knowledge-work-plugins`; path: `data/skills/write-query/SKILL.md`; commit: `8444efcd48f7012f09797778a36a33e73d0861f4`; SHA-256: `4c7ef791db1f23504c457cc52de0d8855d26f176d5acf037260deb1b98e5e34e`; review status: `FULL_ENTRYPOINT_READ`
  - Declared license in task audit: **Apache-2.0**. The exact upstream root notice is copied in the quarantine folder. The active method is independently authored; only selected entrypoint/support files in the SHA manifest are retained as data. The exact entrypoint and selected personally read support are copied as data-only references under `references/upstream/`; their byte hashes and source commits are in `references/upstream-copy-manifest.json`. These copies are not enabled skill fragments. No upstream script or source code is adopted or executed.
  - Contribution: Translate request into output columns, filters, aggregation and joins; present query and assumptions, not execution proof.
  - Defect/repair: Do not query, export, or modify a database without explicit scope and read/write authorization.; Do not assume internal connectors or schema context exist; ask for access/input only when needed.

## Support closure status

Every direct linked support has a defensible disposition. The listed method-critical references were personally read; remaining scripts/assets/references are inventory-only and not adopted. This is not source-code, live API, legal/clinical currentness, or license admission.

- Direct linked supports: 4; personally read method-critical supports: 0; inventory-only/not adopted: 4.
- Scripts executed: **No**. Scripts and assets not adopted remain inventory-only data; no upstream script or generator was run.
- Any future adaptation needs exact notice preservation, source/code review, and any license disposition required before release. No release/license admission is implied here.

- Notice recorded by audit: `anthropics/knowledge-work-plugins` — `Apache-2.0` — Preserve the repository copyright/license notice if source text or code is adapted.

## Exact-copy manifest

`references/upstream-copy-manifest.json` records every retained entrypoint/support file and copied root license/notice file with source repository, pinned checkout commit, original path, copy path, byte count, and SHA-256. The original audit SHA is cross-checked for every entrypoint. Source copies remain inert provenance data, excluded from routing and execution.
