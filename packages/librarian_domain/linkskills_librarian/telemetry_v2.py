"""Privacy-bounded telemetry validation and aggregation helpers."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import re
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
    "calendar",
    "email",
    "drive",
    "battery",
    "selfie",
    "image",
    "identifier",
    "location",
    "schedule",
    "messages",
    "private_data",
    "private_memory",
    "medical",
    "raw_prompt",
    "raw_transcript",
    "raw_output",
    "file_path",
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
OPTIONAL_FIELDS = {
    "issue",
    "duration_ms",
    "receipt_ref",
    "privacy_findings",
    "effects",
    "feedback",
}
FEEDBACK_FIELDS = {"kind", "rating", "friction", "missing_step", "outcome", "redacted"}
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _contains_prohibited(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key).lower()
            if name == "privacy" and isinstance(item, Mapping):
                if any(_contains_prohibited(child) for child_key, child in item.items() if child_key not in {"raw_content", "prohibited_content"}):
                    return True
                continue
            if any(token in name for token in FORBIDDEN) or _contains_prohibited(item):
                return True
        return False
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
    if (
        not isinstance(report.get(field), str)
        or not report[field].strip()
        or len(report[field].strip()) > 256
    ):
        raise ValueError(f"required_{field}")


def _bounded_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or len(value) > 32:
        raise ValueError(f"invalid_{field}")
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 120:
            raise ValueError(f"invalid_{field}")
        result.append(item.strip())
    return result


def _validate_feedback(value: Any) -> None:
    if not isinstance(value, dict) or set(value) - FEEDBACK_FIELDS:
        raise ValueError("invalid_feedback")
    if value.get("redacted") is not True:
        raise ValueError("feedback_must_be_redacted")
    for key in set(value) - {"redacted"}:
        item = value[key]
        if not isinstance(item, (str, int, float, bool)) or (isinstance(item, str) and len(item) > 120):
            raise ValueError("invalid_feedback")


def validate_report(report: dict) -> None:
    """Validate the complete privacy-bounded telemetry contract."""
    if not isinstance(report, dict):
        raise ValueError("invalid_report")
    if _contains_prohibited(report):
        raise ValueError("prohibited_content")
    if not REQUIRED_FIELDS.issubset(report):
        raise ValueError("required_field")
    unknown = set(report) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        raise ValueError("unknown_field")

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

    if not _DIGEST_RE.fullmatch(report["skill_digest"]):
        raise ValueError("invalid_skill_digest")
    if "receipt_ref" in report:
        _require_string(report, "receipt_ref")
    if "duration_ms" in report and (
        isinstance(report["duration_ms"], bool)
        or not isinstance(report["duration_ms"], int)
        or not 0 <= report["duration_ms"] <= 86_400_000
    ):
        raise ValueError("invalid_duration_ms")
    if "privacy_findings" in report:
        _bounded_strings(report["privacy_findings"], "privacy_findings")
    if "effects" in report:
        effects = _bounded_strings(report["effects"], "effects")
        if any(item in {"network", "file_delete", "destructive", "production_mutation"} for item in effects):
            raise ValueError("forbidden_effect")
    if "feedback" in report:
        _validate_feedback(report["feedback"])

    privacy = report["privacy"]
    if (
        not isinstance(privacy, dict)
        or privacy.get("raw_content") is not False
        or privacy.get("prohibited_content") is not False
        or set(privacy) != {"raw_content", "prohibited_content"}
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
            if set(issue) != {"type"}:
                raise ValueError("issue_fields_forbidden")
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
            try:
                byte_size = len(json.dumps(report, ensure_ascii=False).encode("utf-8"))
            except (TypeError, ValueError):
                byte_size = 0
            return {
                "accepted": False,
                "reason": str(exc),
                "byte_size": byte_size,
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
