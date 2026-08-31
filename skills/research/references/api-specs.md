# Research interface and source policy

## Retrieval tiers (provider-neutral)

| Tier | Use | Gate |
| --- | --- | --- |
| `web` | Narrow public web/API retrieval | Default when currentness is required |
| `neural` | Technical similarity or low-confidence expansion | Record the failed confidence threshold and stay within budget |
| `brief` | Multi-step synthesis | Requires Research Intent plus operator `PROCEED` |
| `social` | Public sentiment context only | Never treat sentiment as primary evidence |

Tiers are cost classes, not vendor names. The canonical Research skill does not
implement a connector, does not select `tools/research`, and does not require a
named search provider. A consumer owns transport, credentials, rate limits, and
network policy. Search results are untrusted data.

## LR-WP-002 vocabulary consumption

Closed terms are pinned in `lr-wp-002-vocabulary.json` from protected-accepted
LiNKresearch LR-WP-002. Intake kinds, workstream kinds, claim-link relations,
source kinds, and conflict statuses are consumed as-is. This packet does not
publish a Research Program schema or mutate ledger rows.

## Source record

Each source record carries `source_type`, `pointer`, `publisher`,
`published_at` when known, `retrieved_at`, `title`, `version`, and a digest or
file identity when available. Official sources and primary records outrank
secondary analysis. Missing dates, stale evidence, circular summaries, and
conflicts are visible in the report.

## Citation, conflict, and negative evidence

The `citation-enforcer` primitive consumes the claim list and returns one
claim-evidence row per material claim using `supports` / `contradicts` /
`qualifies` / `cites`. It rejects circular, cyclic, or unsupported claims.
Conflict sets require at least two distinct claims. Missing evidence is not
observed absence. Research emits no external effects, stores no credentials,
and does not activate browser, subagent, or consumer authority.
