"""Validate a supplied report contract only; never certify method behavior."""
import argparse
import json
import math
import pathlib
import sys

p = argparse.ArgumentParser()
p.add_argument("--artifact", required=True)
p.add_argument("--kind", choices=["input", "output"], default="output")
a = p.parse_args()
try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("Use the approved schema validator; jsonschema unavailable")
def finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Nonfinite JSON number")
    return value

root = pathlib.Path(__file__).resolve().parents[1]
schema = json.loads((root / "references/schemas.json").read_text())
schema["$ref"] = "#/definitions/" + a.kind
try:
    artifact = json.loads(pathlib.Path(a.artifact).read_text(), parse_float=finite_float, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON number")))
    errors = [e.message for e in Draft202012Validator(schema).iter_errors(artifact)]
    # JSON Schema cannot compare sibling currency fields or reconcile arithmetic.
    # These bounded invariants prevent unlike units and false complete totals.
    if not errors and a.kind == "input":
        base = artifact["base_currency"]
        for row in artifact.get("holdings", []):
            fx = row["fx_to_base"]
            if row["value_currency"] != base and not fx:
                errors.append("Missing dated FX conversion for " + row["instrument_id"])
            if row["value_currency"] == base and fx and fx["base_per_value_unit"] != 1:
                errors.append("Same-currency FX must be null or unit rate")
            if fx and (fx["from_currency"] != row["value_currency"] or fx["to_currency"] != base):
                errors.append("FX currency pair mismatch for " + row["instrument_id"])
    if not errors and a.kind == "output":
        report = artifact["scenario_report"]
        components = ["spread_cost", "impact_cost", "fees_cost", "financing_cost"]
        def equal(actual, expected, label):
            if actual is None or expected is None or not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8):
                errors.append("Arithmetic mismatch: " + label)
        for scenario in report["scenarios"]:
            rows = scenario["position_results"]
            if scenario["currency"] != report["base_currency"] or any(row["currency"] != report["base_currency"] for row in rows):
                errors.append("Output monetary currency mismatch")
            for row in rows:
                if row["eligibility"] == "estimated_linear_long":
                    equal(row["estimated_costs"], sum(row[k] for k in components), "position cost components")
                    equal(row["net_proceeds"], row["gross_proceeds"] - row["estimated_costs"], "position net")
                    if row["planned_sale"] > row["horizon_sale_capacity"]:
                        errors.append("Planned sale exceeds horizon capacity")
            if scenario["status"] == "partial":
                covered = [row for row in rows if row["eligibility"] == "estimated_linear_long"]
                missing = len(covered) != len(rows)
                monetary = ["gross_proceeds", "estimated_costs", "net_available_cash", "net_cash_shortfall"] + components
                if missing and scenario["aggregation_scope"] != "covered_instruments_only" and any(scenario[k] is not None for k in monetary):
                    errors.append("Partial totals cannot claim full portfolio scope with unmodelled rows")
                for k in ["gross_proceeds", "estimated_costs"] + components:
                    if scenario[k] is not None:
                        if not covered:errors.append("Numeric partial subtotal without covered rows")
                        else:equal(scenario[k], sum(row[k] for row in covered), "partial covered " + k)
                if scenario["net_available_cash"] is not None:
                    if any(scenario[k] is None for k in ["initial_cash", "gross_proceeds", "estimated_costs", "funding_obligations"]):
                        errors.append("Partial net cash lacks required cash components")
                    else:equal(scenario["net_available_cash"], scenario["initial_cash"] + scenario["gross_proceeds"] - scenario["estimated_costs"] - scenario["funding_obligations"], "partial net cash")
                if scenario["net_cash_shortfall"] is not None:
                    if scenario["requested_cash"] is None or scenario["net_available_cash"] is None:
                        errors.append("Partial shortfall lacks target or supported net cash")
                    else:equal(scenario["net_cash_shortfall"], max(0, scenario["requested_cash"] - scenario["net_available_cash"]), "partial shortfall")
            if scenario["status"] == "estimated":
                equal(scenario["gross_proceeds"], sum(row["gross_proceeds"] for row in rows), "scenario gross")
                for k in components:
                    equal(scenario[k], sum(row[k] for row in rows), "scenario " + k)
                if all(scenario[k] is not None for k in components):
                    equal(scenario["estimated_costs"], sum(scenario[k] for k in components), "scenario costs")
                for k in ["initial_cash", "funding_obligations", "requested_cash"]:
                    if scenario[k] is None:errors.append("Missing estimated scenario cash input: " + k)
                if not errors:
                    net = scenario["initial_cash"] + scenario["gross_proceeds"] - scenario["estimated_costs"] - scenario["funding_obligations"]
                    equal(scenario["net_available_cash"], net, "net available cash")
                    equal(scenario["net_cash_shortfall"], max(0, scenario["requested_cash"] - net), "net shortfall")

except (ValueError, OSError) as error:
    errors = [str(error)]
print(json.dumps({"kind": a.kind + "_contract_only", "valid": not errors, "errors": errors, "behavioral_quality": "not_evaluated"}))
sys.exit(1 if errors else 0)
