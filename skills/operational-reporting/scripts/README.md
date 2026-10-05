# Operational reporting helper

`helper_tool.py` validates a local JSON report input and emits a deterministic
JSON summary. It does not query a calendar, mailbox, battery, health system, or
agent; it does not send or mutate anything.

```bash
python3 scripts/helper_tool.py --input report.json --mode validate
python3 scripts/helper_tool.py --input report.json --mode render-no-change
```


### Trading performance calculation

`helper_tool.py --mode calculate-trading-performance` validates a `trading_performance` input against `references/schemas.json`, then calculates the equity bridge and supplied closed-cohort metrics with `Decimal`. Monetary inputs and outputs are decimal strings. Each non-base-currency amount needs an explicit base-per-source FX rate, effective at the event or mark timestamp, with a source pointer. Fees are positive expenses subtracted from gross realized P&L once; incomplete fee coverage keeps net realized P&L unknown. Deposits and withdrawals are signed cash flows; realized and unrealized P&L stay separate. The result is advisory, has empty external-effects arrays, and does not place orders or establish edge. The `trading-performance-*` evaluator cases run the calculator on fixtures rather than returning canned statuses.


The trading-performance calculator requires every non-null `source_pointer` and `fx_source` to appear verbatim in the input evidence list. It rejects duplicate unrealized `mark_id` values and requires each start/end mark timestamp to equal the report period's start/end. Input decimal strings are limited to 80 characters; calculated output decimal strings allow 500 characters to hold exact bounded products and sums without truncation. The evidence and output pointer arrays allow up to 20,000 rows to cover the bounded 5,000-event input arrays.
