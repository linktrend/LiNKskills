# Fictional worked example

Synthetic values demonstrate a descriptive calculation only. They do not represent a real dataset or a behavioral evaluation. The output has no fiction-only required field.

## Input

```json
{
  "question": "Describe the observed durations.",
  "analysis_mode": "descriptive",
  "estimand": "arithmetic mean of the observed three values only",
  "decision": "sample description, no population decision",
  "data_manifest": {
    "source_ref": "FIC-DATA-1",
    "as_of": "fictional",
    "row_count": 3,
    "column_names": [
      "duration"
    ],
    "version": "synthetic-v1",
    "sampling_frame": "three illustrative observations"
  },
  "variables": [
    {
      "name": "duration",
      "role": "outcome",
      "data_type": "continuous",
      "units": "minutes",
      "measurement_definition": "elapsed minutes",
      "time_window": "none"
    }
  ],
  "sampling_design": {
    "observation_unit": "one fictional observation",
    "target_population": "not specified",
    "sampling_method": "illustrative values",
    "assignment_mechanism": "none",
    "randomization": "none"
  },
  "grouping_and_dependence": {
    "grouping_variables": [],
    "cluster_id": null,
    "repeated_measures": false,
    "time_key": null,
    "dependence_basis": "unknown"
  },
  "missingness": {
    "missing_fields": [],
    "counts_by_variable": {
      "duration": 0
    },
    "mechanism_assumptions": [],
    "handling_plan": "none missing in supplied values"
  },
  "time_structure": {
    "ordered": false,
    "frequency": null,
    "window": null,
    "serial_dependence": "not assessed"
  },
  "prespecified_choices": {
    "alpha": null,
    "power_target": null,
    "multiplicity_family": null,
    "transformations": [],
    "exclusions": [],
    "method_constraints": [
      "descriptive only"
    ]
  }
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "example": {
    "status": "complete",
    "design_checks": [
      {
        "check": "unit definition",
        "finding": "duration recorded in minutes",
        "action": "retain unit",
        "evidence_ref": "FIC-DATA-1"
      },
      {
        "check": "missingness",
        "finding": "0 of 3 values missing",
        "action": "no missing-value handling",
        "evidence_ref": "FIC-DATA-1"
      }
    ],
    "method_choice": {
      "analysis_mode": "descriptive",
      "selected_method": "mean, median and range",
      "rationale": "summarize the observed values without inferring a target population",
      "assumptions": [
        "Values are expressed in minutes."
      ],
      "alternatives_considered": [
        "Median alone if outlier robustness were the priority."
      ],
      "diagnostics": [
        {
          "name": "sorted values",
          "result": "4.0, 6.0, 8.0",
          "interpretation": "symmetric around 6.0 in this three-value fixture."
        }
      ]
    },
    "estimates": [
      {
        "estimand": "mean of observed values",
        "group": null,
        "comparator": null,
        "estimate": 6.0,
        "effect_measure": "arithmetic mean",
        "unit": "minutes",
        "n": 3,
        "sample_counts": {
          "observed": 3,
          "missing": 0
        },
        "standard_error": null,
        "interval": null,
        "p_value": null,
        "multiplicity": {
          "family_size": null,
          "adjustment": null,
          "adjusted_p_value": null
        },
        "provenance": {
          "source_ref": "FIC-DATA-1",
          "data_version": "synthetic-v1",
          "formula_or_code": "(4.0+6.0+8.0)/3",
          "analysis_timestamp": "fictional"
        },
        "uncomputed_reason": "No inferential estimand or sampling design was supplied; no interval or test is claimed."
      }
    ],
    "descriptive_summary": [
      {
        "variable": "duration",
        "group": null,
        "n": 3,
        "missing_n": 0,
        "mean": 6.0,
        "median": 6.0,
        "standard_deviation": 2.0,
        "minimum": 4.0,
        "maximum": 8.0,
        "unit": "minutes",
        "formula_or_definition": "mean; median; sample standard deviation (n\u22121)",
        "provenance": {
          "source_ref": "FIC-DATA-1",
          "data_version": "synthetic-v1",
          "formula_or_code": "values=[4.0,6.0,8.0]",
          "analysis_timestamp": "fictional"
        }
      }
    ],
    "model_results": [],
    "power_analysis": {
      "status": "not_applicable",
      "target_effect": null,
      "effect_unit": null,
      "alpha": null,
      "target_power": null,
      "variance_or_event_rate": null,
      "allocation_ratio": null,
      "attrition_rate": null,
      "required_n": null,
      "assumptions": [],
      "method": null,
      "uncomputed_reason": "Descriptive task only."
    },
    "interpretation": "For these three fictional observations, mean and median are 6.0 minutes. This describes the supplied values only.",
    "causal_limits": "No comparison or intervention; no causal conclusion.",
    "multiplicity_and_model_diagnostics": [],
    "limitations": [
      "Synthetic illustration.",
      "Representativeness and independence are unknown."
    ],
    "gaps": [
      "No inferential design or target population supplied."
    ],
    "owner_handoff": []
  }
}
```
