"""Strict schema allowlisting, size limits, and redaction before persistence."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional, Set

from .retention import redact_payload, should_redact_key

DEFAULT_MAX_PAYLOAD_BYTES = 64_000
DEFAULT_MAX_STRING_CHARS = 8_000

FEEDBACK_ALLOWED_KEYS = frozenset(
    {
        "skill_id",
        "run_id",
        "kind",
        "rating",
        "friction",
        "missing_step",
        "outcome",
        "notes",
        "idempotency_key",
    }
)

TRACE_ALLOWED_KEYS = frozenset(
    {
        "skill_id",
        "run_id",
        "summary",
        "observed",
        "fingerprint",
        "idempotency_key",
    }
)

FORBIDDEN_TOP_LEVEL = frozenset(
    {
        "secret",
        "secrets",
        "password",
        "token",
        "api_key",
        "authorization",
        "conversation",
        "conversation_transcript",
        "brain_data",
        "brain_transcript",
        "brain_memory",
        "reasoning",
        "hidden_reasoning",
        "messages",
        "raw_prompt",
    }
)

RUN_MUTATION_ALLOWED = frozenset(
    {
        "run_id",
        "progress",
        "disclosure",
        "validation",
        "artifact_refs",
        "classification",
        "output",
        "evidence",
        "feedback",
        "error_class",
        "message",
        "trace_to_eval_eligible",
        "details",
        "idempotency_key",
    }
)


class PayloadValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _byte_size(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, default=str).encode("utf-8"))


def _reject_forbidden_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        name = str(key)
        if name.lower() in FORBIDDEN_TOP_LEVEL or should_redact_key(name):
            raise PayloadValidationError(
                "payload_forbidden_field",
                f"forbidden or secret-bearing field rejected: {name}",
            )


def _reject_oversized_strings(value: Any, *, limit: int, path: str = "$") -> None:
    if isinstance(value, str):
        if len(value) > limit:
            raise PayloadValidationError(
                "payload_too_large",
                f"string at {path} exceeds {limit} characters",
            )
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_oversized_strings(child, limit=limit, path=f"{path}.{key}")
        return
    if isinstance(value, list):
        for idx, child in enumerate(value):
            _reject_oversized_strings(child, limit=limit, path=f"{path}[{idx}]")


def allowlist_and_redact(
    params: Mapping[str, Any],
    *,
    allowed_keys: Set[str],
    max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
    max_string_chars: int = DEFAULT_MAX_STRING_CHARS,
    require_keys: Optional[Set[str]] = None,
) -> dict[str, Any]:
    """Reject unexpected/forbidden fields, enforce size, redact, return clean dict."""
    if not isinstance(params, Mapping):
        raise PayloadValidationError("payload_invalid", "payload must be an object")

    _reject_forbidden_keys(params)
    unknown = sorted(set(params.keys()) - allowed_keys)
    if unknown:
        raise PayloadValidationError(
            "payload_unexpected_field",
            "unexpected fields rejected: " + ", ".join(unknown),
        )
    if require_keys:
        missing = sorted(require_keys - set(params.keys()))
        if missing:
            raise PayloadValidationError(
                "payload_missing_field",
                "missing required fields: " + ", ".join(missing),
            )

    if _byte_size(dict(params)) > max_bytes:
        raise PayloadValidationError(
            "payload_too_large",
            f"payload exceeds {max_bytes} bytes",
        )
    _reject_oversized_strings(params, limit=max_string_chars)

    cleaned = {k: params[k] for k in params if k in allowed_keys}
    return redact_payload(cleaned)


def prepare_feedback_params(params: Mapping[str, Any]) -> dict[str, Any]:
    return allowlist_and_redact(
        params,
        allowed_keys=FEEDBACK_ALLOWED_KEYS,
        require_keys={"run_id", "skill_id"},
    )


def prepare_trace_params(params: Mapping[str, Any]) -> dict[str, Any]:
    return allowlist_and_redact(
        params,
        allowed_keys=TRACE_ALLOWED_KEYS,
        require_keys={"run_id", "skill_id", "summary"},
    )


def prepare_run_mutation_params(params: Mapping[str, Any]) -> dict[str, Any]:
    return allowlist_and_redact(
        params,
        allowed_keys=RUN_MUTATION_ALLOWED,
        require_keys={"run_id"},
    )
