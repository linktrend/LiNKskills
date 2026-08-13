"""Privacy-bounded telemetry validation and aggregation helpers."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from typing import Any


FORBIDDEN = {
    "prompt",
    "transcript",
    "conversation",
    "secret",
    "credential",
    "raw_output",
    "customer",
    "case",
    "lead",
    "portfolio",
    "reasoning",
    "chain_of_thought",
    "source_code",
    "repository",
    "attachment",
    "binary",
    "health",
    "media",
    "brain_memory",
}
REQUIRED_FIELDS = {
    "report_kind",
    "score",
    "skill_release_ref",
    "skill_version",
    "skill_digest",
    "consumer_class",
    "actor_class",
    "runtime_profile_ref",
    "compatibility",
    "outcome",
    "occurred_at",
    "received_at",
    "idempotency_key",
    "source_fingerprint",
    "privacy",
    "retention_class",
}


def _contains_prohibited(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            any(token in str(key).lower() for token in FORBIDDEN) or _contains_prohibited(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_prohibited(item) for item in value)
    return False


def canonical_digest(report: dict) -> str:
    """Return the server-computed digest for a JSON telemetry report."""
    encoded = json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_string(report: dict, field: str) -> None:
    if not isinstance(report.get(field), str) or not report[field].strip():
        raise ValueError(f"required_{field}")


def validate_report(report: dict) -> None:
    """Validate the complete privacy-bounded telemetry contract."""
    if not isinstance(report, dict):
        raise ValueError("invalid_report")
    if _contains_prohibited(report):
        raise ValueError("prohibited_content")
    if not REQUIRED_FIELDS.issubset(report):
        raise ValueError("required_field")

    for field in (
        "skill_release_ref",
        "skill_version",
        "skill_digest",
        "consumer_class",
        "actor_class",
        "runtime_profile_ref",
        "compatibility",
        "outcome",
        "occurred_at",
        "received_at",
        "idempotency_key",
        "source_fingerprint",
        "retention_class",
    ):
        _require_string(report, field)

    privacy = report["privacy"]
    if (
        not isinstance(privacy, dict)
        or privacy.get("raw_content") is not False
        or privacy.get("prohibited_content") is not False
    ):
        raise ValueError("privacy_fields_required")

    score = report["score"]
    if score is not None and (isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 10):
        raise ValueError("invalid_score")

    kind = report["report_kind"]
    issue = report.get("issue")
    if kind == "completed_use":
        if score is None:
            raise ValueError("completed_score_required")
        if score == 10 and any(key in report for key in ("issue", "narrative", "fragment")):
            raise ValueError("perfect_use_diagnostics_forbidden")
        if score < 10 and not isinstance(issue, dict):
            raise ValueError("typed_issue_required")
        if isinstance(issue, dict):
            _require_string(issue, "type")
    elif kind in {"non_use", "retrieval_failure", "not_evaluated"}:
        if score is not None or "issue" in report:
            raise ValueError("non_use_fields_forbidden")
    else:
        raise ValueError("invalid_report_kind")


class TelemetryPort:
    """Accept idempotent telemetry without retaining submitted report bodies."""

    def __init__(self) -> None:
        self._receipts: dict[str, dict[str, str]] = {}
        self._events: list[tuple[str, str, str, str, str, str]] = []

    def submit(self, report: dict) -> dict:
        """Validate and accept a report, returning a privacy-safe receipt."""
        try:
            validate_report(report)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            digest = canonical_digest(report) if isinstance(report, dict) else None
            return {
                "accepted": False,
                "reason": str(exc),
                "byte_size": len(json.dumps(report, ensure_ascii=False).encode("utf-8")),
                "digest": digest,
            }

        key = report["idempotency_key"]
        digest = canonical_digest(report)
        previous = self._receipts.get(key)
        if previous is not None:
            if previous["digest"] != digest:
                raise ValueError("idempotency_conflict")
            return dict(previous)

        receipt = {
            "accepted": True,
            "receipt_id": "receipt:" + digest[7:23],
            "digest": digest,
        }
        self._receipts[key] = receipt
        issue_type = (report.get("issue") or {}).get("type", "none")
        self._events.append(
            (
                report["skill_release_ref"],
                report["consumer_class"],
                report["actor_class"],
                report["runtime_profile_ref"],
                report["compatibility"],
                issue_type,
            )
        )
        return dict(receipt)

    def aggregate(self) -> dict[tuple[str, str, str, str, str, str], int]:
        """Count accepted events by the six permitted aggregate dimensions."""
        result: dict[tuple[str, str, str, str, str, str], int] = {}
        for event in self._events:
            result[event] = result.get(event, 0) + 1
        return result


def classification(issue_type: str | None) -> str:
    """Map a bounded issue type to its Librarian classification."""
    return {
        "incompatible": "runtime_incompatibility",
        "unavailable": "missing_dependency",
        "incorrect": "skill_defect",
    }.get(issue_type or "", "insufficient_evidence")
