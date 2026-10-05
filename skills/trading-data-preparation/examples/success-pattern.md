# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "lineage": {
    "source_snapshot": "fictional-ES-1m-v2",
    "schema_version": "bars-v1",
    "instrument": "ES fictional front contract",
    "calendar": "CME session, fictional calendar version"
  },
  "row_counts": {
    "input": 3,
    "output": 2,
    "residual": 1
  },
  "coverage": {
    "requested_minutes": 3,
    "observed_minutes": 2,
    "timezone": "UTC"
  },
  "bars": {
    "target_frequency": "2m",
    "label": "right-closed",
    "partial_final_bar": true,
    "vwap_window": "session"
  },
  "gaps": [
    "Minute 00:01 absent; no fill applied."
  ],
  "synthetic_rows": [],
  "rolls": {
    "raw_contracts_preserved": true,
    "adjustment": "none",
    "executable_levels_from_adjusted": false
  },
  "units": {
    "price": "USD/index point",
    "volume": "contracts"
  },
  "validations": [
    "OHLC ordering valid for observed rows.",
    "Input volume 17 contracts; output 12 plus 5 documented residual/partial-window volume."
  ],
  "limitations": [
    "Fictional worked example; source market data not inspected."
  ]
}
```
