"""Sanitised durable-store readiness diagnostics. Fail closed; never leak secrets."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .migration_package import LIVE_RECOVERY_OWNER

_URI_RE = re.compile(r"(?i)\b(?:postgres(?:ql)?|https?|redis|amqp|mysql)://[^\s'\"\\]+")
_KEYVAL_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|dsn|database_url|"
    r"connection_string|ssl(mode|rootcert|key|cert)|user|host|port|dbname|"
    r"linkskills_database_url|linkskills_postgres_url|linkskills_store_url)"
    r"\s*[:=]\s*\S+"
)
_USERINFO_RE = re.compile(r"(?i)\b[\w.+-]+://[^/\s:]+:[^/\s@]+@")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?\b")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)

_REDACTED = "[redacted]"

READY_FALSE = {
    "ready": False,
    "fail_closed": True,
    "live_apply": False,
}


def redact_store_text(value: str | None) -> str:
    """Strip URIs, credential key/values, addresses, and userinfo from text."""
    if not value:
        return ""
    text = _URI_RE.sub(_REDACTED, value)
    text = _USERINFO_RE.sub(_REDACTED, text)
    text = _KEYVAL_RE.sub(lambda match: f"{match.group(1)}={_REDACTED}", text)
    text = _IPV4_RE.sub(_REDACTED, text)
    text = _EMAIL_RE.sub(_REDACTED, text)
    return text


def _sqlstate(exc: BaseException) -> str:
    state = getattr(exc, "sqlstate", None)
    if state:
        return str(state)
    diag = getattr(exc, "diag", None)
    if diag is not None and getattr(diag, "sqlstate", None):
        return str(diag.sqlstate)
    return ""


def classify_store_exception(exc: BaseException) -> str:
    """Map a store exception to a stable, non-secret readiness code."""
    state = _sqlstate(exc)
    name = type(exc).__name__
    raw = str(exc).lower()
    if state == "42P01" or "undefinedtable" in name.lower() or "does not exist" in raw:
        return "store_schema_missing"
    if (
        state == "42501"
        or "insufficientprivilege" in name.lower()
        or "permission denied" in raw
        or "row-level security" in raw
    ):
        return "store_privilege_denied"
    if name in {"OperationalError", "InterfaceError"}:
        if "password authentication" in raw or "authentication failed" in raw:
            return "store_auth_failed"
        return "store_unreachable"
    if "auth" in raw and "password authentication" in raw:
        return "store_auth_failed"
    if "digest mismatch" in raw or "fingerprint" in raw:
        return "store_fingerprint_mismatch"
    if "postgres" in raw and ("version" in raw or "incompatible" in raw):
        return "store_incompatible_postgres"
    return "store_not_ready"


_ACTIONS = {
    "store_schema_missing": (
        "Required lskills relations are missing. Platform must apply the "
        "hash-bound production store package (000002-000013) under recovery "
        f"task {LIVE_RECOVERY_OWNER}."
    ),
    "store_privilege_denied": (
        "Runtime role lacks a required grant or RLS predicate failed closed. "
        "Platform must verify least-privilege grants for svc_lskills_runtime; "
        "do not widen to BYPASSRLS or service_role."
    ),
    "store_auth_failed": (
        "Store authentication failed. Platform must rotate or render the "
        "runtime SecretRef; Skills must not print or substitute credentials."
    ),
    "store_unreachable": (
        "Durable store is unreachable. Platform must restore network, listener, "
        "and SecretRef rendering. Skills must not invent a DSN or apply live DDL."
    ),
    "store_fingerprint_mismatch": (
        "Applied SQL fingerprints do not match the Skills-owned package digest. "
        "Stop writes; Platform must reconcile backups and the exact package."
    ),
    "store_incompatible_postgres": (
        "Server major version is not PostgreSQL 17. Platform must apply this "
        "package only on a compatible PostgreSQL 17 instance."
    ),
    "store_memory_not_production": (
        "In-memory persistence is source-proof only and is not a production store."
    ),
    "store_not_ready": (
        "Durable store failed closed. Platform must inspect apply/backup receipts "
        "without sharing secrets with Skills workers."
    ),
}


def diagnose_store_exception(exc: BaseException) -> dict[str, Any]:
    """Return sanitised, actionable readiness diagnostics. Always fail closed."""
    code = classify_store_exception(exc)
    return {
        **READY_FALSE,
        "code": code,
        "redacted_error": type(exc).__name__,
        "actionable": _ACTIONS[code],
        "does_not_include": "dsn_credentials_host_or_sqlstate_detail",
    }


def diagnose_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    """Interpret a binder snapshot without copying secret-bearing fields."""
    if not snapshot:
        return {
            **READY_FALSE,
            "code": "store_schema_missing",
            "redacted_error": "missing_snapshot",
            "actionable": _ACTIONS["store_schema_missing"],
        }
    ready = bool(snapshot.get("ready"))
    missing = snapshot.get("missing_relations") or []
    pg_major = snapshot.get("postgres_major")
    if ready and not missing and pg_major == 17:
        package = snapshot.get("package") or {}
        return {
            "ready": True,
            "fail_closed": True,
            "live_apply": False,
            "code": "store_ready_ephemeral_or_applied",
            "package_id": package.get("package_id"),
            "package_version": package.get("package_version"),
            "payload_digest_sha256": package.get("payload_digest_sha256"),
            "postgres_major": pg_major,
            "actionable": "Runtime may perform granted operations only; live apply remains Platform-owned.",
        }
    if pg_major not in (None, 17):
        return {
            **READY_FALSE,
            "code": "store_incompatible_postgres",
            "redacted_error": "incompatible_postgres_major",
            "actionable": _ACTIONS["store_incompatible_postgres"],
        }
    if missing:
        return {
            **READY_FALSE,
            "code": "store_schema_missing",
            "redacted_error": "missing_relations",
            "missing_relation_count": len(list(missing)),
            "actionable": _ACTIONS["store_schema_missing"],
        }
    return {
        **READY_FALSE,
        "code": "store_not_ready",
        "redacted_error": "snapshot_not_ready",
        "actionable": _ACTIONS["store_not_ready"],
    }


def memory_store_readiness() -> dict[str, Any]:
    """Memory adapters are never production-ready."""
    return {
        **READY_FALSE,
        "code": "store_memory_not_production",
        "redacted_error": "MemoryStore",
        "actionable": _ACTIONS["store_memory_not_production"],
    }
