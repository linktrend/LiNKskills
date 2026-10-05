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
    "reconstruction": [
      {
        "wallet_or_group": "fictional cohort A",
        "swaps": 12,
        "transfers": 4,
        "lp_actions": 1,
        "airdrops": 0,
        "open_inventory": 120.0,
        "unresolved_events": 2,
        "evidence_refs": [
          "synthetic_fixture.csv rows 1-19"
        ]
      }
    ],
    "metrics": [
      {
        "wallet_or_group": "fictional cohort A",
        "sample_window": "2026-01-01 to 2026-03-31",
        "denominator": 8,
        "value": 0.25,
        "metric": "net profitable closed lots fraction",
        "currency_or_unit": "fraction",
        "limitations": [
          "Synthetic example only; eight lots do not establish edge."
        ]
      }
    ],
    "behavior_hypotheses": [
      {
        "label": "short-horizon activity possible",
        "observable_basis": [
          "Median closed-lot duration 8 minutes across 8 lots."
        ],
        "alternative_explanations": [
          "Missing/open inventory; API timestamp resolution unknown."
        ],
        "confidence_limits": [
          "Descriptive only."
        ]
      }
    ],
    "concentration_checks": [
      {
        "measure": "single-token share of closed-lot gross P&L",
        "value": 0.7,
        "leave_one_out": -15.0,
        "denominator": "4 tokens; amounts in fictional USD",
        "limitations": [
          "mark and fees are illustrative"
        ]
      }
    ],
    "coordination_indicators": [
      {
        "indicator": "two wallets share a funder and bought within a 2-slot window",
        "possible_interpretation": "possible operational link only",
        "false_positives": [
          "exchange hot wallet",
          "shared custodian",
          "automated market maker"
        ],
        "evidence_refs": [
          "synthetic_fixture.csv rows 20-21"
        ]
      }
    ],
    "gaps": [
      "Provider P&L not reconciled for the two unresolved events."
    ],
    "recommendation": "Monitor as an informational candidate only if owner criteria permit; no copy or action."
  },
  "status": "fictional_example_not_evaluation"
}
```
