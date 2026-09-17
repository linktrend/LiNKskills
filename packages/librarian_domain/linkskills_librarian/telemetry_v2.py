"""Privacy-bounded telemetry validation and aggregation helpers."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
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
    "tenant_id",
    "user_id",
    "email",
    "consumer_correlation",
    "conversation_id",
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
    "opaque_correlation",
}
ALLOWED_DOMAINS = frozenset({"linkskills", "lskills", "skills"})
CROSS_DOMAIN = frozenset(
    {"linkbrain", "brain", "linbrain", "linklibraries", "libraries"}
)
OPAQUE_CORR_RE = re.compile(r"^corr:[0-9a-f]{16,64}$")
RETENTION_WINDOWS = {
    "ephemeral": timedelta(0),
    "minimal": timedelta(days=7),
    "standard": timedelta(days=30),
    "audit": timedelta(days=90),
}
MAX_METRIC_CARDINALITY = 256
OVERFLOW_DIMENSIONS = ("*", "*", "*", "*", "*", "overflow")


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


def opaque_correlation_from(raw: str) -> str:
    """Hash a raw consumer correlation into an opaque Skills-only reference."""
    material = str(raw or "").strip().encode("utf-8")
    digest = hashlib.sha256(b"linkskills-corr-v1:" + material).hexdigest()[:32]
    return "corr:" + digest


def _require_string(report: dict, field: str) -> None:
    if not isinstance(report.get(field), str) or not report[field].strip():
        raise ValueError(f"required_{field}")


def _parse_occurred_at(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def retained_until_for(occurred_at: str, retention_class: str) -> datetime:
    """Return the exclusive expiry instant for a retention class."""
    window = RETENTION_WINDOWS.get(retention_class)
    if window is None:
        raise ValueError("invalid_retention_class")
    return _parse_occurred_at(occurred_at) + window


def validate_report(report: dict) -> None:
    """Validate the complete privacy-bounded telemetry contract."""
    if not isinstance(report, dict):
        raise ValueError("invalid_report")
    if _contains_prohibited(report):
        raise ValueError("prohibited_content")
    domain = str(report.get("domain") or report.get("domain_key") or "linkskills").strip().lower()
    if domain in CROSS_DOMAIN:
        raise ValueError("cross_domain_rejected")
    if domain not in ALLOWED_DOMAINS:
        raise ValueError("cross_domain_rejected")
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
        "opaque_correlation",
    ):
        _require_string(report, field)

    if not OPAQUE_CORR_RE.fullmatch(report["opaque_correlation"]):
        raise ValueError("invalid_opaque_correlation")
    if report["retention_class"] not in RETENTION_WINDOWS:
        raise ValueError("invalid_retention_class")
    _parse_occurred_at(report["occurred_at"])

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
    elif kind in {"non_use", "retrieval_failure", "not_evaluated", "feedback"}:
        if kind != "feedback" and (score is not None or "issue" in report):
            raise ValueError("non_use_fields_forbidden")
        if kind == "feedback" and not isinstance(issue, dict):
            raise ValueError("typed_issue_required")
        if kind == "feedback" and isinstance(issue, dict):
            _require_string(issue, "type")
    else:
        raise ValueError("invalid_report_kind")


def bind_use_or_feedback_report(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a use/feedback payload to exact release/profile and opaque correlation.

    Raw consumer correlation is hashed and dropped. The returned report is the
    only object that may be submitted to :class:`TelemetryPort`.
    """
    report = dict(payload)
    raw = report.pop("consumer_correlation", None)
    if raw is not None and not isinstance(raw, str):
        raise ValueError("invalid_consumer_correlation")
    derived = opaque_correlation_from(raw) if raw else None
    existing = report.get("opaque_correlation")
    if derived and existing and existing != derived:
        raise ValueError("correlation_mismatch")
    if derived:
        report["opaque_correlation"] = derived
    report.setdefault("domain", "linkskills")
    report.setdefault("domain_key", "linkskills")
    return report


class TelemetryPort:
    """Accept idempotent telemetry without retaining submitted report bodies."""

    def __init__(self, *, max_cardinality: int = MAX_METRIC_CARDINALITY) -> None:
        self._receipts: dict[str, dict[str, str]] = {}
        self._events: list[dict[str, Any]] = []
        self.max_cardinality = max_cardinality

    def submit(self, report: dict) -> dict:
        """Validate and accept a report, returning a privacy-safe receipt."""
        try:
            bound = bind_use_or_feedback_report(report)
            validate_report(bound)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            digest = canonical_digest(report) if isinstance(report, dict) else None
            return {
                "accepted": False,
                "reason": str(exc),
                "byte_size": len(json.dumps(report, ensure_ascii=False).encode("utf-8")),
                "digest": digest,
            }

        key = bound["idempotency_key"]
        digest = canonical_digest(bound)
        previous = self._receipts.get(key)
        if previous is not None:
            if previous["digest"] != digest:
                raise ValueError("idempotency_conflict")
            return dict(previous)

        expiry = retained_until_for(bound["occurred_at"], bound["retention_class"])
        receipt = {
            "accepted": True,
            "receipt_id": "receipt:" + digest[7:23],
            "digest": digest,
            "skill_release_ref": bound["skill_release_ref"],
            "runtime_profile_ref": bound["runtime_profile_ref"],
            "skill_digest": bound["skill_digest"],
            "opaque_correlation": bound["opaque_correlation"],
            "retention_class": bound["retention_class"],
            "retained_until": expiry.isoformat().replace("+00:00", "Z"),
        }
        self._receipts[key] = receipt
        issue_type = (bound.get("issue") or {}).get("type", "none")
        self._events.append(
            {
                "dimensions": (
                    bound["skill_release_ref"],
                    bound["consumer_class"],
                    bound["actor_class"],
                    bound["runtime_profile_ref"],
                    bound["compatibility"],
                    issue_type,
                ),
                "occurred_at": bound["occurred_at"],
                "retention_class": bound["retention_class"],
                "digest": digest,
                "opaque_correlation": bound["opaque_correlation"],
                "idempotency_key": key,
            }
        )
        return dict(receipt)

    def aggregate(self) -> dict[tuple[str, str, str, str, str, str], int]:
        """Count accepted events by the six permitted aggregate dimensions."""
        result: dict[tuple[str, str, str, str, str, str], int] = {}
        overflow = 0
        for event in self._events:
            dims = event["dimensions"]
            if dims in result or len(result) < self.max_cardinality:
                result[dims] = result.get(dims, 0) + 1
            else:
                overflow += 1
        if overflow:
            result[OVERFLOW_DIMENSIONS] = result.get(OVERFLOW_DIMENSIONS, 0) + overflow
        return result

    def purge(self, *, now: datetime | None = None) -> dict[str, int]:
        """Drop expired receipts and events. Does not restore purged bodies."""
        clock = now or datetime.now(timezone.utc)
        kept_events: list[dict[str, Any]] = []
        expired_keys: set[str] = set()
        for event in self._events:
            expiry = retained_until_for(event["occurred_at"], event["retention_class"])
            if expiry <= clock:
                expired_keys.add(event["idempotency_key"])
            else:
                kept_events.append(event)
        purged_events = len(self._events) - len(kept_events)
        self._events = kept_events
        purged_receipts = 0
        for key in list(self._receipts):
            if key in expired_keys:
                del self._receipts[key]
                purged_receipts += 1
        return {"purged_events": purged_events, "purged_receipts": purged_receipts, "retained": len(self._events)}


def classification(issue_type: str | None) -> str:
    """Map a bounded issue type to its Librarian classification."""
    return {
        "incompatible": "runtime_incompatibility",
        "unavailable": "missing_dependency",
        "incorrect": "skill_defect",
    }.get(issue_type or "", "insufficient_evidence")
