#!/usr/bin/env python3
"""Validate supplied operational reporting records without external effects."""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "contracts"))
from linkskills_contracts.validate import validate_instance

ROOT = Path(__file__).resolve().parents[1]

MODES = {"executive_digest", "flash_report", "no_material_change", "supervised_agent_summary", "maintenance_result", "trading_performance"}
PRIVATE_MARKERS = ("customer_email", "customer_phone", "password", "api_key", "secret", "selfie")



def _decimal(value: Any, label: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a finite decimal string") from exc
    if not result.is_finite():
        raise ValueError(f"{label} must be finite")
    return result


def _timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an ISO timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def _convert(row: dict[str, Any], amount_key: str, event_time: str, base: str, label: str) -> Decimal | None:
    amount = row.get(amount_key)
    rate = row.get("fx_to_base")
    rate_time = row.get("fx_effective_at")
    source = row.get("fx_source")
    if amount is None or rate is None or rate_time is None or not source:
        return None
    if not row.get("source_pointer"):
        raise ValueError(f"{label} requires source_pointer")
    fx = _decimal(rate, f"{label}.fx_to_base")
    if fx <= 0:
        raise ValueError(f"{label}.fx_to_base must be positive")
    if row.get("currency") == base and fx != Decimal("1"):
        raise ValueError(f"{label} base-currency FX rate must equal 1")
    if _timestamp(rate_time, f"{label}.fx_effective_at") != _timestamp(event_time, f"{label}.event_time"):
        raise ValueError(f"{label} FX effective time must equal the event or valuation time")
    return _decimal(amount, f"{label}.{amount_key}") * fx


def _money_total(rows: list[dict[str, Any]], amount_key: str, time_key: str, base: str, label: str, *, signed: bool) -> tuple[Decimal | None, list[str]]:
    total = Decimal(0)
    gaps: list[str] = []
    seen: set[str] = set()
    for i, row in enumerate(rows):
        ident = str(row.get("flow_id") or row.get("event_id") or row.get("fee_id") or row.get("mark_id") or row.get("funding_id") or i)
        if ident in seen:
            raise ValueError(f"duplicate {label} id: {ident}")
        seen.add(ident)
        converted = _convert(row, amount_key, row[time_key], base, f"{label}[{ident}]")
        if converted is None:
            gaps.append(f"{label} {ident} lacks amount or exact-time FX evidence")
            continue
        if not signed and converted < 0:
            raise ValueError(f"{label} {ident} must be nonnegative")
        total += converted
    return (None if gaps else total), gaps


def calculate_trading_performance(payload: dict[str, Any]) -> dict[str, Any]:
    """Calculate with exact source/additive arithmetic and bounded Decimal precision."""
    with localcontext() as context:
        # Input strings are capped at 80 chars; 600 digits covers risk products and
        # 5,000-row sums without intermediate rounding. Ratios round only at output.
        context.prec = 600
        return _calculate_trading_performance(payload)


def _calculate_trading_performance(payload: dict[str, Any]) -> dict[str, Any]:
    """Calculate the report body under the caller's high-precision context."""
    if payload.get("mode") != "trading_performance":
        raise ValueError("mode must be trading_performance")
    data = payload.get("trading_performance")
    if not isinstance(data, dict):
        raise ValueError("trading_performance object is required")
    evidence = data.get("evidence")
    if not isinstance(evidence, list) or any(not isinstance(item, str) for item in evidence):
        raise ValueError("evidence must list source references as strings")
    evidence_set = set(evidence)
    refs: set[str] = set()
    def collect_refs(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"source_pointer", "fx_source"} and isinstance(child, str) and child:
                    refs.add(child)
                else:
                    collect_refs(child)
        elif isinstance(value, list):
            for child in value:
                collect_refs(child)
    collect_refs({key: value for key, value in data.items() if key != "evidence"})
    missing_refs = sorted(refs - evidence_set)
    if missing_refs:
        raise ValueError("missing evidence reference: " + ", ".join(missing_refs[:20]))
    base = str(data["base_currency"])
    period = data["period"]
    start = _timestamp(period["start_inclusive"], "period.start_inclusive")
    end = _timestamp(period["end_exclusive"], "period.end_exclusive")
    if start >= end:
        raise ValueError("period must have start before end")
    def in_period(row: dict[str, Any], key: str) -> bool:
        stamp = _timestamp(row[key], key)
        return start <= stamp < end
    flows = [r for r in data["cash_flows"] if in_period(r, "occurred_at")]
    realized = [r for r in data["realized_pnl"] if in_period(r, "occurred_at")]
    fees = [r for r in data["fees"] if in_period(r, "occurred_at")]
    funding = [r for r in data["funding"] if in_period(r, "occurred_at")]
    unknowns: list[str] = []
    cash_flow, g = _money_total(flows, "amount", "occurred_at", base, "cash_flow", signed=True); unknowns += g
    gross_realized, g = _money_total(realized, "amount", "occurred_at", base, "realized_pnl", signed=True); unknowns += g
    fee_total, g = _money_total(fees, "amount", "occurred_at", base, "fee", signed=False); unknowns += g
    for fee in fees:
        if fee["deduction_basis"] == "already_net_of_realized_pnl":
            raise ValueError(f"fee {fee['fee_id']} contradicts gross_before_fees basis; refusing double deduction")
        if fee["deduction_basis"] == "unknown":
            unknowns.append(f"fee {fee['fee_id']} deduction basis is unknown")
            fee_total = None
    funding_total, g = _money_total(funding, "amount", "occurred_at", base, "funding", signed=True); unknowns += g
    if data["cost_coverage"] != "complete":
        unknowns.append("fee coverage is not complete")
        fee_total = None
    if data["coverage"] != "complete":
        unknowns.append("overall source coverage is not complete")
        cash_flow = None
        gross_realized = None
        funding_total = None
    net_realized = None if None in (gross_realized, fee_total, funding_total) or data["cost_coverage"] != "complete" or data["coverage"] != "complete" else gross_realized - fee_total + funding_total
    def snapshot(row: dict[str, Any], label: str) -> Decimal | None:
        return _convert(row, "amount", row["as_of"], base, label)
    if _timestamp(data["starting_equity"]["as_of"], "starting_equity.as_of") != start:
        raise ValueError("starting equity valuation time must equal period start")
    if _timestamp(data["ending_equity"]["as_of"], "ending_equity.as_of") != end:
        raise ValueError("ending equity valuation time must equal period end")
    start_eq = snapshot(data["starting_equity"], "starting_equity")
    end_eq = snapshot(data["ending_equity"], "ending_equity")
    if start_eq is None or end_eq is None or data["equity_coverage"] != "complete":
        unknowns.append("starting or ending equity lacks complete amount/FX coverage")
    cash_components: list[Decimal] = []
    cash_gaps: list[str] = []
    for row in data["cash_flows"]:
        if not in_period(row, "occurred_at"): continue
        value = _convert(row, "amount", row["occurred_at"], base, f"cash_flow[{row['flow_id']}]")
        if value is None: cash_gaps.append(row["flow_id"]); continue
        if row["kind"] == "deposit" and value < 0: raise ValueError("deposit must be positive")
        if row["kind"] == "withdrawal" and value > 0: raise ValueError("withdrawal must be negative")
        cash_components.append(value)
    cash_flow = None if cash_gaps or data["coverage"] != "complete" else sum(cash_components, Decimal(0))
    unrealized = Decimal(0); unrealized_gaps=[]; mark_ids=set()
    for row in data["unrealized_pnl_changes"]:
        mark_id=row["mark_id"]
        if mark_id in mark_ids: raise ValueError(f"duplicate unrealized mark_id: {mark_id}")
        mark_ids.add(mark_id)
        a=row["start_mark"]; b=row["end_mark"]
        if _timestamp(a["as_of"], f"unrealized[{mark_id}].start_mark.as_of") != start:
            raise ValueError(f"unrealized mark {mark_id} start_mark as_of must equal period start")
        if _timestamp(b["as_of"], f"unrealized[{mark_id}].end_mark.as_of") != end:
            raise ValueError(f"unrealized mark {mark_id} end_mark as_of must equal period end")
        va=_convert(a,"amount",a["as_of"],base,f"unrealized[{mark_id}].start")
        vb=_convert(b,"amount",b["as_of"],base,f"unrealized[{mark_id}].end")
        if va is None or vb is None: unrealized_gaps.append(row["mark_id"]); continue
        unrealized += vb-va
    unrealized_total = None if unrealized_gaps or data["coverage"] != "complete" else unrealized
    if unrealized_total is None: unknowns.append("unrealized P&L change lacks complete start/end marks or FX")
    expected_end = None if any(v is None for v in (start_eq,cash_flow,net_realized,unrealized_total)) else start_eq+cash_flow+net_realized+unrealized_total
    residual = None if expected_end is None or end_eq is None else end_eq-expected_end
    cohorts=[]
    cohort_ids=set()
    for row in data["closed_cohorts"]:
        if not in_period(row,"closed_at"): continue
        tid=row["trade_id"]
        if tid in cohort_ids: raise ValueError(f"duplicate closed cohort trade_id: {tid}")
        cohort_ids.add(tid)
        pnl=None if row["net_pnl_base"] is None else _decimal(row["net_pnl_base"],f"cohort[{tid}].net_pnl_base")
        cohorts.append((row,pnl))
    known=[pnl for _,pnl in cohorts if pnl is not None]
    unknown_n=len(cohorts)-len(known)
    wins=sum(1 for v in known if v>0); losses=sum(1 for v in known if v<0); breakeven=sum(1 for v in known if v==0)
    total_closed=len(cohorts)
    if unknown_n: unknowns.append(f"{unknown_n} closed cohort(s) have unknown net P&L")
    cohort_sum=sum(known,Decimal(0)) if unknown_n==0 else None
    mean=_divide(cohort_sum,Decimal(total_closed)) if cohort_sum is not None and total_closed else None
    all_rate=_divide(Decimal(wins),Decimal(total_closed)) if unknown_n==0 and total_closed else None
    decided= wins+losses
    decided_rate=_divide(Decimal(wins),Decimal(decided)) if unknown_n==0 and decided else None
    gross_wins=sum((v for v in known if v>0),Decimal(0)); gross_losses=abs(sum((v for v in known if v<0),Decimal(0)))
    pf=None if unknown_n or gross_losses==0 else _divide(gross_wins,gross_losses)
    r_rows=[]
    for row,pnl in cohorts:
        terms=row.get("initial_risk")
        if terms is None or pnl is None:
            reason='net P&L or initial-risk evidence missing'
            if pnl is not None and terms is None:
                unknowns.append(f"initial risk missing for closed cohort {row['trade_id']}")
            r_rows.append({'trade_id':row['trade_id'],'initial_risk_base':None,'net_pnl_base':_fmt(pnl),'r_multiple':None,'undefined_reason':reason}); continue
        side=terms['side']; entry=_decimal(terms['entry_price'],'entry_price'); stop=_decimal(terms['original_stop'],'original_stop')
        if (side=='long' and stop>=entry) or (side=='short' and stop<=entry): raise ValueError(f"{row['trade_id']} original stop is not on the loss side")
        fx=_decimal(terms['fx_to_base'],'risk.fx_to_base')
        if fx<=0: raise ValueError('risk.fx_to_base must be positive')
        if terms['quote_currency']==base and fx!=Decimal('1'): raise ValueError('base-currency risk FX rate must equal 1')
        if _timestamp(terms['fx_effective_at'],'risk.fx_effective_at')!=_timestamp(terms['entry_at'],'risk.entry_at'):
            raise ValueError('risk FX effective time must equal entry_at')
        risk=abs(entry-stop)*_decimal(terms['quantity'],'risk.quantity')*_decimal(terms['contract_multiplier'],'risk.contract_multiplier')*_decimal(terms['point_value_per_price_unit_per_contract'],'risk.point_value')*fx
        if risk<=0: raise ValueError('initial risk must be positive')
        r_rows.append({'trade_id':row['trade_id'],'initial_risk_base':_fmt(risk),'net_pnl_base':_fmt(pnl),'r_multiple':_fmt(_divide(pnl,risk)),'undefined_reason':None})
    period_s=f"[{period['start_inclusive']}, {period['end_exclusive']}), {period['timezone']}"
    return {'division_precision':'18 significant digits, ROUND_HALF_EVEN; exact numerator and denominator retained','period':period_s,'base_currency':base,'coverage':data['coverage'],'cash_flow_base':_fmt(cash_flow),'realized_gross_pnl_base':_fmt(gross_realized),'fee_expense_base':_fmt(fee_total),'funding_base':_fmt(funding_total),'net_realized_pnl_base':_fmt(net_realized),'unrealized_pnl_change_base':_fmt(unrealized_total),'starting_equity_base':_fmt(start_eq),'expected_ending_equity_base':_fmt(expected_end),'observed_ending_equity_base':_fmt(end_eq),'equity_residual_base':_fmt(residual),'equity_reconciled':bool(residual==0 and data['coverage']=='complete' and data['equity_coverage']=='complete'),'closed_count':total_closed,'known_closed_count':len(known),'unknown_closed_count':unknown_n,'closed_cohort_net_pnl_base':_fmt(cohort_sum),'mean_net_pnl_per_closed_trade_base':_fmt(mean),'all_closed_win_rate':_ratio(all_rate,str(wins),str(total_closed) if unknown_n==0 else None,'positive net closed outcomes / all closed outcomes including breakeven', 'unknown closed outcomes prevent a complete denominator' if unknown_n else ('no closed cohort' if not total_closed else None)),'decided_win_rate':_ratio(decided_rate,str(wins),str(decided) if unknown_n==0 else None,'positive outcomes / positive plus negative; breakeven excluded','unknown closed outcomes prevent a complete denominator' if unknown_n else ('no wins or losses' if not decided else None)),'profit_factor':_ratio(pf,_fmt(gross_wins),_fmt(gross_losses),'sum positive net cohort P&L / absolute sum negative net cohort P&L','unknown outcomes prevent calculation' if unknown_n else ('no loss denominator; PF is undefined, not infinity' if gross_losses==0 else None)),'r_by_trade':r_rows,'unknowns':sorted(set(unknowns)),'source_pointers':sorted(evidence_set)}


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 18
        context.rounding = ROUND_HALF_EVEN
        return numerator / denominator


def _fmt(value: Decimal | None) -> str | None:
    if value is None:
        return None
    text = format(value, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return '0' if text in {'', '-0'} else text


def _ratio(value: Decimal | None, numerator: str | None, denominator: str | None, basis: str, reason: str | None) -> dict[str, Any]:
    return {'value':_fmt(value),'numerator':numerator,'denominator':denominator,'basis':basis,'undefined_reason':reason}


def build_trading_performance_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Calculate and validate the bounded no-effects output envelope."""
    calculated = calculate_trading_performance(payload)
    report = {"status": "READY_FOR_OWNER" if calculated["equity_reconciled"] and not calculated["unknowns"] else "DRAFT", "mode": "trading_performance", "message": "Supplied-record calculation; advisory report only. No order, approval, or causal conclusion is authorized.", "sections": ["Equity reconciliation", "Realized and unrealized P&L", "Closed-cohort metrics", "Risk and unknowns"], "evidence": payload["trading_performance"]["evidence"], "uncertainty": calculated["unknowns"], "effects": {"messages_sent": [], "external_calls": [], "mutations": []}, "trading_performance": calculated}
    schemas = json.loads((ROOT / "references" / "schemas.json").read_text(encoding="utf-8"))
    checked = validate_instance(report, {"$ref": "#/definitions/output", "definitions": schemas["definitions"]})
    if checked.errors:
        raise ValueError("calculated output failed schema: " + "; ".join(str(item) for item in checked.errors))
    return report

def validate(payload: dict[str, Any]) -> list[str]:
    """Return stable validation errors for supplied report inputs."""
    errors: list[str] = []
    if payload.get("mode") not in MODES:
        errors.append("mode is not supported")
    if payload.get("window") not in {"morning", "evening", "custom"}:
        errors.append("window must be morning, evening, or custom")
    if not isinstance(payload.get("records"), list):
        errors.append("records must be an array")
    else:
        for index, record in enumerate(payload["records"]):
            if not isinstance(record, dict):
                errors.append(f"records[{index}] must be an object")
                continue
            if record.get("status") == "verified_completed" and not record.get("evidence_pointer"):
                errors.append(f"records[{index}] verified_completed requires evidence_pointer")
            if record.get("kind") == "mail" and record.get("is_own_mailbox") is not True:
                errors.append(f"records[{index}] mail must be explicitly own mailbox")
            if record.get("is_routine") is True:
                errors.append(f"records[{index}] Routine records must be omitted")
    encoded = json.dumps(payload, sort_keys=True)
    if payload.get("mode") == "trading_performance":
        try:
            schemas = json.loads((ROOT / "references" / "schemas.json").read_text(encoding="utf-8"))
            checked = validate_instance(payload, {"$ref": "#/definitions/input", "definitions": schemas["definitions"]})
            errors.extend(str(item) for item in checked.errors)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            errors.append(f"trading_performance schema unavailable or invalid: {exc}")
    if any(re.search(rf"\b{re.escape(marker)}\b", encoded, re.IGNORECASE) for marker in PRIVATE_MARKERS):
        errors.append("private, health, or selfie marker is not allowed")
    return sorted(set(errors))


def main() -> int:
    """Run validation or deterministic one-line rendering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", choices=("validate", "render-no-change", "calculate-trading-performance"), default="validate")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        errors = validate(payload)
        calculated = calculate_trading_performance(payload) if not errors and args.mode == "calculate-trading-performance" else None
        result: dict[str, Any] = {"status": "FAILED" if errors else "SUCCESS", "errors": errors, "effects": {"messages_sent": [], "external_calls": [], "mutations": []}}
        if args.mode == "calculate-trading-performance" and not errors:
            report = {"status": "READY_FOR_OWNER" if calculated["equity_reconciled"] and not calculated["unknowns"] else "DRAFT", "mode": "trading_performance", "message": "Supplied-record calculation; advisory report only. No order, approval, or causal conclusion is authorized.", "sections": ["Equity reconciliation", "Realized and unrealized P&L", "Closed-cohort metrics", "Risk and unknowns"], "evidence": payload["trading_performance"]["evidence"], "uncertainty": calculated["unknowns"], "effects": {"messages_sent": [], "external_calls": [], "mutations": []}, "trading_performance": calculated}
            output_schemas = json.loads((ROOT / "references" / "schemas.json").read_text(encoding="utf-8"))
            output_check = validate_instance(report, {"$ref": "#/definitions/output", "definitions": output_schemas["definitions"]})
            if output_check.errors:
                raise ValueError("calculated output failed schema: " + "; ".join(str(item) for item in output_check.errors))
            result = report
        if args.mode == "render-no-change" and not errors:
            if payload.get("mode") != "no_material_change":
                result = {"status": "FAILED", "errors": ["render-no-change requires no_material_change mode"], "effects": {"messages_sent": [], "external_calls": [], "mutations": []}}
            else:
                result["message"] = "No material verified change in the supplied window."
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in {"SUCCESS", "DRAFT", "READY_FOR_OWNER"} else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "errors": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
