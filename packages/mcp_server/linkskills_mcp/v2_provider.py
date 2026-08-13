"""Stateless, provider-only MCP 2026-07-28 boundary.

This module is deliberately a boundary validator, not a skill executor or
selector.  A production caller supplies the Platform-backed verifier; tests use
the small deterministic verifier seam below.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable, Mapping

RESOURCE_OPERATIONS = (
    "skills_capabilities_get", "skills_catalog_list", "skills_catalog_search",
    "skills_release_list", "skills_release_describe", "skills_qualification_get",
    "skills_release_entrypoint_get", "skills_release_sections_list", "skills_release_section_get",
    "skills_release_resources_list", "skills_release_resource_get", "skills_release_content_get",
    "skills_release_package_get",
)
TOOLS = (
    "skills_release_verify", "skills_use_report_submit", "skills_use_report_status_get",
    "skills_feedback_submit", "skills_feedback_status_get", "skills_librarian_status_get",
)
CATALOG_OPERATIONS = frozenset(("skills_capabilities_get", "skills_catalog_list", "skills_catalog_search"))

@dataclass(frozen=True)
class TrustedIdentity:
    """Minimal already-verified Platform identity used by the provider."""
    org_id: str
    actor_id: str
    audience: str
    capabilities: frozenset[str]
    binding: str


def _resource_record(operation: str) -> dict[str, str]:
    suffix = operation.removeprefix("skills_").replace("_get", "").replace("_list", "")
    return {"name": operation, "uri_template": f"skills://v2/{suffix}/{{snapshot_id}}"}


class V2Provider:
    """Fail-closed request gate with stable catalogue snapshot cursors."""
    def __init__(self, verifier: Callable[[str], TrustedIdentity] | None = None, *, catalog_version: str = "catalog-v2") -> None:
        self._verifier = verifier or (lambda _: (_ for _ in ()).throw(ValueError("verifier_required")))
        self._snapshot_id = "snapshot:" + sha256(catalog_version.encode()).hexdigest()[:16]

    def resources(self) -> tuple[dict[str, str], ...]: return tuple(_resource_record(op) for op in RESOURCE_OPERATIONS)
    def tools(self) -> tuple[str, ...]: return TOOLS

    def _identity(self, authorization: Any) -> TrustedIdentity:
        if not isinstance(authorization, str) or not authorization:
            raise ValueError("auth_required")
        try:
            identity = self._verifier(authorization)
        except Exception as exc:  # verifier error is deliberately opaque
            raise ValueError("auth_invalid") from exc
        if not isinstance(identity, TrustedIdentity) or not identity.org_id or not identity.actor_id or not identity.binding:
            raise ValueError("auth_invalid")
        if identity.audience != "lskills-api" or "skills.read" not in identity.capabilities:
            raise ValueError("forbidden")
        return identity

    def _cursor(self, cursor: Any) -> int:
        if cursor is None: return 0
        if not isinstance(cursor, str): raise ValueError("cursor_invalid")
        parts = cursor.split(":")
        if len(parts) != 3 or f"{parts[0]}:{parts[1]}" != self._snapshot_id:
            raise ValueError("cursor_snapshot_mismatch")
        try: return int(parts[2])
        except ValueError as exc: raise ValueError("cursor_invalid") from exc

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("protocol_version") != "2026-07-28": return {"ok": False, "error": "contract_incompatible"}
        if any(key in request for key in ("session", "session_id")) or request.get("operation") == "initialize":
            return {"ok": False, "error": "session_not_supported"}
        operation = request.get("operation")
        if not isinstance(operation, str): return {"ok": False, "error": "unsupported_operation"}
        if operation.startswith("skills_run_") or operation.startswith("skills_tool_"):
            return {"ok": False, "error": "legacy_execution_disabled"}
        if operation not in RESOURCE_OPERATIONS + TOOLS: return {"ok": False, "error": "unsupported_operation"}
        try: self._identity(request.get("authorization"))
        except ValueError as exc: return {"ok": False, "error": str(exc)}
        if operation in TOOLS: return {"ok": True, "kind": "tool", "operation": operation}
        limit = request.get("limit", 50)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            return {"ok": False, "error": "validation_failed"}
        try: offset = self._cursor(request.get("cursor"))
        except ValueError as exc: return {"ok": False, "error": str(exc)}
        result: dict[str, Any] = {"ok": True, "kind": "resource", "operation": operation, "snapshot_id": self._snapshot_id, "cursor": f"{self._snapshot_id}:{offset}", "limit": limit, "no_fallback": True}
        if operation not in CATALOG_OPERATIONS:
            skill_id, version = request.get("skill_id"), request.get("version")
            if not isinstance(skill_id, str) or not skill_id or not isinstance(version, str) or not version:
                return {"ok": False, "error": "exact_release_required"}
            result.update({"skill_id": skill_id, "version": version})
        return result


class ModernSkillsMcpServer:
    """JSON-RPC facade with no initialize handshake and no server-side session."""
    protocol_version = "2026-07-28"
    def __init__(self, provider: V2Provider) -> None: self.provider = provider
    def handle_rpc(self, message: Mapping[str, Any]) -> dict[str, Any] | None:
        req_id = message.get("id")
        if req_id is None: return None
        method, params = message.get("method"), message.get("params") or {}
        if method == "initialize": return self._error(req_id, "session_not_supported")
        if not isinstance(params, Mapping): return self._error(req_id, "validation_failed")
        authorization = (params.get("_meta") or {}).get("authorization") if isinstance(params.get("_meta"), Mapping) else params.get("authorization")
        if method == "resources/list":
            response = self.provider.handle({"protocol_version": self.protocol_version, "authorization": authorization, "operation": "skills_capabilities_get"})
            return self._result(req_id, {"resources": list(self.provider.resources())} if response["ok"] else response)
        if method == "tools/list":
            response = self.provider.handle({"protocol_version": self.protocol_version, "authorization": authorization, "operation": "skills_release_verify"})
            return self._result(req_id, {"tools": list(self.provider.tools())} if response["ok"] else response)
        if method == "resources/read":
            request = dict(params); request.update({"protocol_version": self.protocol_version, "authorization": authorization, "operation": params.get("operation")})
            response = self.provider.handle(request)
            return self._result(req_id, {"contents": [], "structuredContent": response, "isError": not response["ok"]})
        if method == "tools/call":
            response = self.provider.handle({"protocol_version": self.protocol_version, "authorization": authorization, "operation": params.get("name")})
            return self._result(req_id, {"structuredContent": response, "isError": not response["ok"]})
        return self._error(req_id, "unsupported_operation")
    @staticmethod
    def _result(req_id: object, value: object) -> dict[str, Any]: return {"jsonrpc": "2.0", "id": req_id, "result": value}
    @staticmethod
    def _error(req_id: object, code: str) -> dict[str, Any]: return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": code}}
