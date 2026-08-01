"""Strict schema allowlisting, size limits, and recursive privacy redaction."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Optional, Set

from .retention import REDACTED, redact_payload, should_redact_key

DEFAULT_MAX_PAYLOAD_BYTES = 64_000
DEFAULT_MAX_STRING_CHARS = 8_000
REDACTED_UNKNOWN = "[REDACTED:unknown_content]"

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
        "prompt",
        "prompts",
        "credentials",
        "credential",
        "auth",
        "bearer",
        "cookie",
    }
)

# Nested privacy categories that must be rejected/redacted at any depth.
# Bare structural names like run-mutation ``output`` are handled via allowlists;
# nested ``input``/``output``/``prompt``/conversation/credential keys still match.
_PRIVACY_CATEGORY_RE = re.compile(
    r"("
    r"secret|password|passwd|token|api[_-]?key|authorization|credential|"
    r"bearer|cookie|oauth|"
    r"conversation|transcript|messages|chat[_-]?history|"
    r"brain([_-]?data|[_-]?transcript|[_-]?memory)?|"
    r"prompt|raw[_-]?prompt|system[_-]?prompt|"
    r"reasoning|hidden[_-]?reasoning|chain[_-]?of[_-]?thought|"
    r"(^|[_-])(raw[_-]?)?input($|[_-])|(^|[_-])(raw[_-]?)?output($|[_-])|"
    r"completion|private[_-]?key|access[_-]?key|session[_-]?token"
    r")",
    re.IGNORECASE,
)

_CONTENT_BEARING_UNKNOWN_RE = re.compile(
    r"(content|body|text|payload|blob|message|prompt|output|input|data|"
    r"transcript|memory|conversation|completion)",
    re.IGNORECASE,
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


def is_privacy_category_key(key: str) -> bool:
    name = str(key)
    if name.lower() in FORBIDDEN_TOP_LEVEL:
        return True
    if should_redact_key(name):
        return True
    return bool(_PRIVACY_CATEGORY_RE.search(name))


def reject_forbidden_privacy(
    value: Any,
    *,
    path: str = "$",
    allowed_keys: Optional[Set[str]] = None,
) -> None:
    """Recursively reject prohibited privacy categories in request payloads.

    Keys present in ``allowed_keys`` are permitted at the current object level
    (structural allowlist), but nested children are still scanned with no
    allowlist exemption.
    """
    if isinstance(value, Mapping):
        for key, child in value.items():
            name = str(key)
            child_path = f"{path}.{name}"
            if allowed_keys is not None and name in allowed_keys:
                reject_forbidden_privacy(child, path=child_path, allowed_keys=None)
                continue
            if is_privacy_category_key(name):
                raise PayloadValidationError(
                    "payload_forbidden_field",
                    f"forbidden or secret-bearing field rejected: {child_path}",
                )
            reject_forbidden_privacy(child, path=child_path, allowed_keys=None)
        return
    if isinstance(value, list):
        for idx, child in enumerate(value):
            reject_forbidden_privacy(child, path=f"{path}[{idx}]", allowed_keys=None)


def sanitize_result_payload(
    value: Any,
    *,
    path: str = "$",
    preserve_keys: Optional[Set[str]] = None,
) -> Any:
    """Recursively redact privacy categories and unknown content-bearing structures.

    ``preserve_keys`` exempts structural allowlisted keys at the current level only.
    """
    if isinstance(value, Mapping):
        out: dict[Any, Any] = {}
        for key, child in value.items():
            name = str(key)
            if preserve_keys is not None and name in preserve_keys:
                out[key] = sanitize_result_payload(child, path=f"{path}.{name}")
                continue
            if is_privacy_category_key(name):
                out[key] = REDACTED
            elif isinstance(child, (dict, list, tuple)):
                out[key] = sanitize_result_payload(child, path=f"{path}.{name}")
            elif isinstance(child, str) and _CONTENT_BEARING_UNKNOWN_RE.search(name):
                # Unknown content-bearing leaf — redact rather than persist.
                out[key] = REDACTED_UNKNOWN
            else:
                out[key] = child
        return out
    if isinstance(value, list):
        return [sanitize_result_payload(item, path=f"{path}[]") for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_result_payload(item, path=f"{path}[]") for item in value)
    return value


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

    # Top-level privacy keys outside the structural allowlist fail closed.
    for key in params:
        name = str(key)
        if name not in allowed_keys and is_privacy_category_key(name):
            raise PayloadValidationError(
                "payload_forbidden_field",
                f"forbidden or secret-bearing field rejected: $.{name}",
            )
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
    # Redact nested privacy inside values; preserve allowlisted structural keys.
    nested_scrubbed = {k: redact_payload(v) for k, v in cleaned.items()}
    return sanitize_result_payload(nested_scrubbed, preserve_keys=allowed_keys)


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
