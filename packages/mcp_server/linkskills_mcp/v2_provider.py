"""Sessionless, provider-only MCP v2 facade.

This is intentionally a contract adapter: it exposes resource identifiers and
validates request shape; it does not execute a Skill Pack or select one.
"""
from __future__ import annotations

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

class V2Provider:
    """Pure request gate for MCP 2026-07-28 semantics."""
    def resources(self) -> tuple[str, ...]: return RESOURCE_OPERATIONS
    def tools(self) -> tuple[str, ...]: return TOOLS
    def handle(self, request: dict) -> dict:
        if request.get("protocol_version") != "2026-07-28": return {"ok": False, "error": "contract_incompatible"}
        if not request.get("authorization"): return {"ok": False, "error": "auth_required"}
        if any(k in request for k in ("session", "session_id")) or request.get("operation") == "initialize": return {"ok": False, "error": "session_not_supported"}
        op = request.get("operation", "")
        if op.startswith("skills_run_") or op.startswith("skills_tool_"): return {"ok": False, "error": "legacy_execution_disabled"}
        if op not in RESOURCE_OPERATIONS + TOOLS: return {"ok": False, "error": "unsupported_operation"}
        if op in RESOURCE_OPERATIONS:
            version = request.get("version")
            if not isinstance(version, str) or not version: return {"ok": False, "error": "exact_release_required"}
            cursor, limit = request.get("cursor"), request.get("limit", 50)
            if not isinstance(limit, int) or not 1 <= limit <= 100: return {"ok": False, "error": "validation_failed"}
            return {"ok": True, "kind": "resource", "operation": op, "version": version, "cursor": cursor, "limit": limit, "no_fallback": True}
        return {"ok": True, "kind": "tool", "operation": op}
