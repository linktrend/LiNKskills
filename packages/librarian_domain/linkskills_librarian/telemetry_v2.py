"""Pure privacy-bounded telemetry and Librarian lineage domain helpers."""
from __future__ import annotations
import hashlib, json

FORBIDDEN = {"prompt", "transcript", "conversation", "secret", "credential", "raw_output", "customer", "case", "lead", "portfolio"}

def canonical_digest(report: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def validate_report(report: dict) -> None:
    if set(report).intersection(FORBIDDEN): raise ValueError("prohibited_content")
    kind, score = report.get("report_kind"), report.get("score")
    if kind == "completed_use":
        if not isinstance(score, int) or not 0 <= score <= 10: raise ValueError("invalid_score")
        if score == 10 and any(k in report for k in ("issue", "narrative", "fragment")): raise ValueError("perfect_use_diagnostics_forbidden")
        if score < 10 and not isinstance(report.get("issue"), dict): raise ValueError("typed_issue_required")
    elif kind == "non_use":
        if "score" in report or "issue" in report: raise ValueError("non_use_fields_forbidden")
    else: raise ValueError("invalid_report_kind")

class TelemetryPort:
    def __init__(self) -> None: self._receipts = {}; self._events = []
    def submit(self, report: dict) -> dict:
        try: validate_report(report)
        except ValueError as exc:
            return {"accepted": False, "reason": str(exc), "byte_size": len(json.dumps(report)), "digest": canonical_digest(report)}
        key, digest = report["idempotency_key"], canonical_digest(report)
        if key in self._receipts:
            if self._receipts[key]["digest"] != digest: raise ValueError("idempotency_conflict")
            return self._receipts[key]
        receipt = {"accepted": True, "receipt_id": "receipt:" + digest[7:23], "digest": digest}; self._receipts[key] = receipt; self._events.append(dict(report)); return receipt
    def aggregate(self) -> dict[tuple, int]:
        result = {}
        for e in self._events:
            key = (e.get("skill_release_ref"), e.get("consumer_class"), e.get("actor_class"), e.get("runtime_profile_ref"), (e.get("issue") or {}).get("type", "none")); result[key] = result.get(key, 0) + 1
        return result

def classification(issue_type: str | None) -> str:
    return {"incompatible":"runtime_incompatibility", "unavailable":"missing_dependency", "incorrect":"skill_defect"}.get(issue_type or "", "insufficient_evidence")
