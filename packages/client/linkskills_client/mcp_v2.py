"""Small standard MCP v2 client seam used by consumer conformance fixtures."""

from __future__ import annotations

import base64
import hashlib
from typing import Any, Callable, Mapping


class McpV2Error(RuntimeError):
    """Raised when an MCP response or exact-resource digest is unsafe."""


class McpV2Client:
    """Transport-neutral MCP v2 client with local exact-byte verification.

    ``transport`` receives one JSON-RPC request and returns its decoded JSON
    response. Keeping the transport injectable lets OpenClaw and test fixtures
    use their own stdio/HTTP implementation without duplicating verification.
    """

    def __init__(self, transport: Callable[[Mapping[str, Any]], Mapping[str, Any]], *, authorization: str) -> None:
        if not callable(transport) or not isinstance(authorization, str) or not authorization:
            raise ValueError("transport_and_authorization_required")
        self._transport = transport
        self._authorization = authorization
        self._request_id = 0

    def _call(self, method: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        self._request_id += 1
        payload = dict(params or {})
        payload.setdefault("_meta", {"authorization": self._authorization})
        response = dict(self._transport({"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": payload}))
        if "error" in response:
            raise McpV2Error(str(response["error"].get("message", "mcp_error")))
        result = response.get("result")
        if not isinstance(result, dict):
            raise McpV2Error("invalid_mcp_result")
        if result.get("isError") or (isinstance(result.get("structuredContent"), Mapping) and not result["structuredContent"].get("ok", True)):
            structured = result.get("structuredContent", result)
            raise McpV2Error(str(structured.get("error", "mcp_denied")))
        return result

    def initialize(self) -> dict[str, Any]:
        """Negotiate the standard MCP v2 protocol and capabilities."""
        return self._call("initialize", {"protocolVersion": "2026-07-28", "clientInfo": {"name": "linkskills-client", "version": "2.0.0"}})

    def list_resources(self) -> list[dict[str, Any]]:
        """Return the provider's bounded resource templates."""
        result = self._call("resources/list")
        resources = result.get("resources")
        if not isinstance(resources, list):
            raise McpV2Error("invalid_resource_list")
        return resources

    def read_exact(self, uri: str, *, expected_digest: str | None = None) -> tuple[bytes, str]:
        """Read one exact resource and verify its returned bytes locally."""
        result = self._call("resources/read", {"uri": uri})
        contents = result.get("contents")
        structured = result.get("structuredContent")
        if not isinstance(contents, list) or len(contents) != 1 or not isinstance(structured, Mapping):
            raise McpV2Error("exact_resource_missing")
        item = contents[0]
        if not isinstance(item, Mapping) or not isinstance(item.get("blob"), str):
            raise McpV2Error("exact_resource_not_binary")
        body = base64.b64decode(item["blob"], validate=True)
        digest = "sha256:" + hashlib.sha256(body).hexdigest()
        declared = structured.get("content_digest")
        if declared != digest or (expected_digest is not None and expected_digest != digest):
            raise McpV2Error("integrity_mismatch")
        return body, digest


StandardMcpV2Client = McpV2Client

__all__ = ["McpV2Client", "McpV2Error", "StandardMcpV2Client"]
