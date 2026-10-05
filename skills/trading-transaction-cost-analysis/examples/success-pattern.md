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
    "derived_trade": {
      "notional": 100000.0,
      "quantity": 1000.0,
      "participation": 0.01,
      "currency": "fictional USD",
      "units_and_formula": "weight change 0.10 \u00d7 NAV 1,000,000 = $100,000; / $100 = 1,000 shares; / $10,000,000 ADV = 1%",
      "limitations": [
        "Illustrative inputs only; not a liquidity guarantee."
      ]
    },
    "cost_components": [
      {
        "name": "spread crossing",
        "entry_bps": 20.0,
        "exit_bps": 20.0,
        "round_trip_bps": 40.0,
        "entry_amount": 200.0,
        "exit_amount": 200.0,
        "round_trip_amount": 400.0,
        "currency": "fictional USD",
        "basis": "full quoted spread 40 bps; half spread per side",
        "evidence_refs": [
          "synthetic_fixture"
        ],
        "limitations": [
          "Illustrative."
        ]
      },
      {
        "name": "commission",
        "entry_bps": 1.0,
        "exit_bps": 1.0,
        "round_trip_bps": 2.0,
        "entry_amount": 10.0,
        "exit_amount": 10.0,
        "round_trip_amount": 20.0,
        "currency": "fictional USD",
        "basis": "per side",
        "evidence_refs": [
          "synthetic_fixture"
        ],
        "limitations": [
          "Illustrative."
        ]
      }
    ],
    "total_cost": {
      "entry_bps": 21.0,
      "exit_bps": 21.0,
      "round_trip_bps": 42.0,
      "round_trip_amount": 420.0,
      "currency": "fictional USD",
      "gross_expected_return_bps": 100.0,
      "net_expected_return_bps": 58.0,
      "double_count_review": [
        "Spread included once per crossing."
      ]
    },
    "sensitivity": [
      {
        "multiple": 1,
        "round_trip_cost_bps": 42,
        "net_expected_return_bps": 58,
        "limitations": [
          "Synthetic."
        ]
      },
      {
        "multiple": 2,
        "round_trip_cost_bps": 84,
        "net_expected_return_bps": 16,
        "limitations": [
          "Synthetic."
        ]
      },
      {
        "multiple": 3,
        "round_trip_cost_bps": 126,
        "net_expected_return_bps": -26,
        "limitations": [
          "Synthetic."
        ]
      }
    ],
    "capacity": {
      "adv_currency": "USD",
      "adv_window": "20 trading sessions",
      "order_participation": 0.01,
      "capacity_status": "below hypothetical 5% participation assumption",
      "limitations": [
        "Assumption not a policy limit."
      ]
    },
    "locate_treatment": "Not applicable; hypothetical long exposure.",
    "gaps": [
      "No real quote, fee schedule, fill or ADV evidence."
    ],
    "owner_handoff": [
      "Eric owns any engine configuration."
    ]
  },
  "status": "fictional_example_not_evaluation"
}
```
