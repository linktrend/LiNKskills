# Fictional successful-shape example

This synthetic example demonstrates the schema shape only. It is not a market observation, completed user task, behavior evaluation, PASS, or certification.

```json
{
  "input": {
    "question": "Synthetic example only; not a market claim.",
    "as_of": "2026-10-05T00:00:00Z",
    "evidence": [
      {
        "source": "synthetic_fixture",
        "retrieved_at": "2026-10-05T00:00:00Z",
        "evidence_ref": "fixture row 1",
        "units": "fictional",
        "limitations": [
          "Illustrative data; not real observations."
        ]
      }
    ]
  },
  "expected_output_shape": {
    "status": "draft_complete",
    "unit_risk": {
      "stop_price": 95.0,
      "per_unit_risk": 5.0,
      "total_initial_risk": 50.0,
      "currency": "fictional USD",
      "formula": "long: (entry 100 - stop 95) \u00d7 quantity 10 \u00d7 multiplier 1",
      "assumptions": [
        "No gap or execution costs in initial risk; modeled values are fictional."
      ]
    },
    "variant_results": [
      {
        "name": "fixed stop",
        "trigger_event": "bar low crossed 95",
        "modeled_fill_price": 93.0,
        "quantity_filled": 10,
        "quantity_remaining": 0,
        "gross_pnl": -70.0,
        "estimated_cost": 2.0,
        "net_pnl": -72.0,
        "currency": "fictional USD",
        "ambiguous_path": true,
        "limitations": [
          "Bar also touched target; sequence unknown; adverse fill chosen for illustration."
        ]
      }
    ],
    "intrabar_ambiguities": [
      "Same OHLC bar crossed stop 95 and target 110; exact event ordering unavailable."
    ],
    "gaps": [
      "No quote/depth or actual fill data."
    ],
    "owner_handoffs": [
      "Risk owner decides whether the hypothetical rule is acceptable."
    ]
  },
  "status": "fictional_example_not_evaluation"
}
```
