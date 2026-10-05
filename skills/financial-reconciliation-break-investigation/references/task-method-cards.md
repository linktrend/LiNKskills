# Reconciliation break investigation cards

The reconciliation skill locates a cause for an already classified break. Matching, cash reconciliation and transaction classification remain separate tasks. Exact upstream task is preserved in `upstream/anthropics--financial-services@574ed3624aeb/plugins/agent-plugins/gl-reconciler/skills/break-trace/SKILL.md`.

## Card A — GL-to-source trace

Anchor the break row and retrieve the specific GL journal/posting and the corresponding subledger/source transaction. Record entry/trade/transaction ID, posting date, source/batch, originating document and relevant fields on each side. Compare transaction date vs settlement/posting date, currency and rate/date, mapping, sign/quantity, duplicate identifiers, and partial/missing amounts. Show `GL value - source value` or the source reconciliation equation; never infer a cause from account names alone.

## Card B — Evidence-supported cause branches

- **Timing/cutoff:** identify the dated item on each side and the cutoff difference; a future clear date requires a dated scheduled reversal/settlement source.
- **FX:** compare base/transaction currencies, applied rate, rate source/date and calculation on both sides; without approved rate evidence, report the differing amounts and request the rate source rather than asserting a correct rate.
- **Mapping:** compare source-to-account mapping table/version with the GL account; without an owner-approved mapping, state the observed accounts and ask reference-data/controller to confirm.
- **Sign/quantity:** compare signed amount, unit, quantity and conversion on source/GL; preserve sign conventions and recompute the resulting difference.
- **Duplicate:** require matching stable transaction IDs or documented duplicate keys and amounts; label as suspected until the duplicate evidence is confirmed.
- **Partial/missing:** enumerate matched/unmatched component rows and sum; distinguish a genuinely missing record from a query/filter/date-scope gap.

## Card C — Result and action contract

Return break key, both source references/values, formula/difference, evidenced cause or competing hypotheses, period impact, proposed owner/evidence request, and expected clear date or `unknown`. Action verbs are proposals only. Source examples use internal MCP names and financial-instrument-specific data; these names are not available capabilities or presumed entity schema. Use currently supplied native schema (including scoped Odoo `odoo__search_records`, `odoo__count_records`, `odoo__read_records` when applicable); do not invent a connector call. Adjustment, suppression or clearing requires the accountable owner and remains outside this skill.
