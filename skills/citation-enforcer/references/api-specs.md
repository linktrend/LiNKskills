# Citation Specs

Claim record fields:
- `claim_id`
- `claim_text`
- `source_type` (`memory` | `search` | `file`)
- `source_pointer`
- `rel` (`supports` | `contradicts` | `qualifies` | `cites`)
- `confidence`
- `freshness_timestamp`

Negative evidence:
- missing pointer → block (`missing`)
- `contradicts` plus pointer → `observed_absence`

Graph rules:
- no self-links, no self-supersession, claim-to-claim DAG
