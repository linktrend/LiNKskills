"""Retention and redaction helpers for telemetry / evidence payloads."""

from __future__ import annotations

import re
from typing import Any

_REDACT_KEY_RE = re.compile(
    r"("
    r"secret|password|passwd|token|api[_-]?key|authorization|credential|auth|"
    r"bearer|cookie|oauth|private[_-]?key|access[_-]?key|session[_-]?token|"
    r"reasoning|hidden[_-]?reasoning|chain[_-]?of[_-]?thought|"
    r"brain([_-]?data|[_-]?transcript|[_-]?memory)?|private[_-]?transcript|"
    r"conversation([_-]?transcript)?|messages|chat[_-]?history|"
    r"prompt|raw[_-]?prompt|system[_-]?prompt|"
    r"(^|[_-])input($|[_-])|(^|[_-])output($|[_-])|completion"
    r")",
    re.IGNORECASE,
)

REDACTED = "[REDACTED]"


def should_redact_key(key: str) -> bool:
    return bool(_REDACT_KEY_RE.search(str(key)))


def redact_payload(value: Any) -> Any:
    """Recursively strip/redact keys matching secret/privacy category patterns."""
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, child in value.items():
            if should_redact_key(str(key)):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_payload(child)
        return redacted
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_payload(item) for item in value)
    return value
