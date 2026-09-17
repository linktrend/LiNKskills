"""HTTP client for production ``skills.api.v0.2`` (exact-byte verification)."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .mcp_v2 import McpV2Error


class HttpV2Client:
    """Stdlib HTTP client for ``POST /v2/{operation}`` with local digest checks."""

    def __init__(self, base_url: str, *, authorization: str, timeout_s: float = 10.0) -> None:
        if not isinstance(base_url, str) or not base_url or not authorization:
            raise ValueError("base_url_and_authorization_required")
        self.base_url = base_url.rstrip("/")
        self._authorization = authorization
        self._timeout_s = timeout_s

    def call(self, operation: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """POST one v2 operation and decode the JSON envelope."""
        body = json.dumps(dict(payload or {}), separators=(",", ":"), sort_keys=True).encode("utf-8")
        request = Request(
            f"{self.base_url}/v2/{operation}",
            data=body,
            method="POST",
            headers={
                "Authorization": self._authorization
                if self._authorization.lower().startswith("bearer ")
                else f"Bearer {self._authorization}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_s) as response:
                raw = response.read()
                parsed = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raw = exc.read()
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except Exception as decode_exc:
                raise McpV2Error(f"http_{exc.code}") from decode_exc
        except URLError as exc:
            raise McpV2Error("gateway_unreachable") from exc
        if not isinstance(parsed, dict):
            raise McpV2Error("invalid_http_result")
        if parsed.get("ok") is False:
            raise McpV2Error(str(parsed.get("error") or "http_denied"))
        return parsed

    def read_exact(
        self,
        operation: str,
        payload: Mapping[str, Any],
        *,
        expected_digest: str | None = None,
    ) -> tuple[bytes, str]:
        """Retrieve one exact resource and verify bytes locally."""
        result = self.call(operation, payload)
        blob = result.get("content_b64")
        if not isinstance(blob, str):
            raise McpV2Error("exact_resource_missing")
        body = base64.b64decode(blob, validate=True)
        digest = "sha256:" + hashlib.sha256(body).hexdigest()
        declared = result.get("content_digest")
        if declared != digest or (expected_digest is not None and expected_digest != digest):
            raise McpV2Error("integrity_mismatch")
        return body, digest


__all__ = ["HttpV2Client"]
