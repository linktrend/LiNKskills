# Fictional worked example

All values and the agreement clause below are synthetic. This reconciles one bounded scenario only; it is not an accounting classification or funding approval.

## Input

```json
{
  "program": "Fictional Sensor R&D",
  "periods": [
    "2026-Q1",
    "2026-Q2"
  ],
  "purpose": "program runway planning",
  "actuals_and_forecasts": [
    {
      "period": "2026-Q1",
      "amount": 10000,
      "currency": "USD",
      "classification": "direct budget",
      "source_ref": "fictional budget v1"
    },
    {
      "period": "2026-Q1",
      "amount": 9000,
      "currency": "USD",
      "classification": "actual direct cost",
      "source_ref": "fictional ledger v1"
    },
    {
      "period": "2026-Q2",
      "amount": 12000,
      "currency": "USD",
      "classification": "direct forecast",
      "source_ref": "fictional forecast v1"
    }
  ],
  "committed_cash": [
    {
      "date": "2026-05-31",
      "amount": 10000,
      "currency": "USD",
      "restriction": "milestone receipt; conditional",
      "status": "scenario only"
    }
  ],
  "funding_restrictions": [
    {
      "source": "fictional award A",
      "amount": 20000,
      "currency": "USD",
      "allowable_scope": [
        "WP1"
      ],
      "source_ref": "fictional award agreement"
    }
  ],
  "rate_authority": {
    "rate": 0.15,
    "base_definition": "modified direct costs excluding equipment",
    "currency": "USD",
    "source_ref": "fictional agreement section 4",
    "effective_period": "2026"
  },
  "milestones": [
    {
      "name": "prototype delivery",
      "date": "2026-05-31",
      "cash_amount": 10000,
      "currency": "USD",
      "condition": "delivery acceptance"
    }
  ],
  "applicable_rules": [
    "Fictional award terms only"
  ],
  "finance_owner": "fictional controller",
  "as_of": "2026-10-05"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "example": {
    "status": "complete",
    "currency_policy": "All rows shown in USD for this fictional case; real outputs retain each source currency and do not convert without an evidenced FX rate.",
    "period_table": [
      {
        "period": "2026-Q1",
        "currency": "USD",
        "direct_budget": 10000,
        "eligible_indirect_base": 8000,
        "indirect_rate": 0.15,
        "indirect_amount": 1200,
        "total_plan": 11200,
        "actual": 9000,
        "forecast": null,
        "variance_actual_minus_plan": -2200,
        "variance_driver": null,
        "basis_source": "fictional approved budget and fictional ledger",
        "restriction_notes": [
          "Award A funds are restricted to WP1; allocation needs controller review."
        ]
      },
      {
        "period": "2026-Q2",
        "currency": "USD",
        "direct_budget": 12000,
        "eligible_indirect_base": 9000,
        "indirect_rate": 0.15,
        "indirect_amount": 1350,
        "total_plan": 13350,
        "actual": null,
        "forecast": 12000,
        "variance_actual_minus_plan": null,
        "variance_driver": null,
        "basis_source": "fictional forecast and fictional agreement",
        "restriction_notes": [
          "Forecast only; no actuals supplied."
        ]
      }
    ],
    "cash_scenarios": [
      {
        "scenario": "base illustration",
        "currency": "USD",
        "opening_unrestricted_cash": 15000,
        "restricted_cash_separate": 20000,
        "receipts": [
          {
            "date": "2026-05-31",
            "amount": 10000,
            "condition": "prototype acceptance; not confirmed",
            "source_ref": "fictional milestone schedule"
          }
        ],
        "outflows": [
          {
            "period": "2026-Q1",
            "amount": 9000,
            "basis": "fictional actual direct outflow",
            "source_ref": "fictional ledger v1"
          },
          {
            "period": "2026-Q2",
            "amount": 13350,
            "basis": "fictional plan including direct and indirect",
            "source_ref": "fictional forecast and rate base"
          }
        ],
        "ending_unrestricted_cash": 2650,
        "formula": "15000 \u2212 9000 \u2212 13350 + 10000 = 2650; restricted cash shown separately and excluded.",
        "status": "conditional scenario, not a cash balance assertion"
      }
    ],
    "exceptions": [
      "The rate, base and restriction are fictional and require actual agreement/controller review."
    ],
    "owner_questions": [
      "Confirm whether milestone receipt is committed and when available."
    ],
    "limitations": [
      "All figures and authorities are fictional.",
      "No accounting classification, award compliance, or funding availability is concluded."
    ],
    "external_actions_taken": false
  }
}
```
