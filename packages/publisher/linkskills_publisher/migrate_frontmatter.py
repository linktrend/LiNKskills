"""Map legacy Skill frontmatter into typed dependency buckets (v0.1).

Does not rewrite on-disk skills. Authors/tests use this helper during migration.
"""

from __future__ import annotations

from typing import Any

KNOWN_PACKAGED_TOOLS = frozenset(
    {
        "ad-intel",
        "asset-filer",
        "doc-engine",
        "fast-playwright",
        "gws",
        "ltr",
        "memory",
        "n8n",
        "n8n-bridge",
        "playwright-cli",
        "research",
        "sandbox",
        "shopify",
        "social-ltr",
        "stripe",
        "sync-scheduler",
        "text-echo",
        "usage",
        "vault",
        "write_file",
        "read_file",
        "list_dir",
        "get_tool_details",
    }
)

KNOWN_EXTERNAL_SERVICES = frozenset(
    {
        "google-workspace",
        "n8n",
        "shopify",
        "stripe",
        "supabase",
    }
)

PERMISSION_TO_CAPABILITY = {
    "fs_read": "filesystem_read",
    "filesystem_read": "filesystem_read",
    "fs_write": "filesystem_write",
    "filesystem_write": "filesystem_write",
    "shell": "shell_exec",
    "shell_exec": "shell_exec",
    "browser": "browser",
    "network": "network",
    "api_access": "network",
    "repository_access": "repository_access",
    "display": "display",
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_id(item: Any) -> str | None:
    if isinstance(item, str):
        text = item.strip()
        return text or None
    if isinstance(item, dict):
        for key in ("id", "name", "tool", "skill"):
            if key in item and item[key]:
                return str(item[key]).strip()
    return None


def migrate_dependencies(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Map legacy ``dependencies[]`` / ``tools`` / ``permissions`` into typed buckets."""
    skill_dependencies: list[dict[str, Any]] = []
    packaged_tools: list[dict[str, Any]] = []
    host_capabilities: list[str] = []
    external_services: list[dict[str, Any]] = []
    library_assets: list[dict[str, Any]] = []
    runtime_requirements: list[dict[str, Any]] = []
    optional_dependencies: list[dict[str, Any]] = []

    seen_tools: set[str] = set()
    seen_skills: set[str] = set()
    seen_services: set[str] = set()
    seen_caps: set[str] = set()

    def add_tool(tool_id: str, *, required: bool = True) -> None:
        if tool_id in seen_tools:
            return
        seen_tools.add(tool_id)
        packaged_tools.append({"id": tool_id, "version": "*", "required": required})

    def add_skill(skill_id: str) -> None:
        if skill_id in seen_skills:
            return
        seen_skills.add(skill_id)
        skill_dependencies.append({"id": skill_id})

    def add_service(service_id: str) -> None:
        if service_id in seen_services:
            return
        seen_services.add(service_id)
        external_services.append({"id": service_id})

    def add_cap(cap: str) -> None:
        if cap in seen_caps:
            return
        seen_caps.add(cap)
        host_capabilities.append(cap)

    for item in _as_list(frontmatter.get("dependencies")):
        dep_id = _normalize_id(item)
        if not dep_id:
            continue
        if dep_id in KNOWN_PACKAGED_TOOLS:
            add_tool(dep_id)
        elif dep_id in KNOWN_EXTERNAL_SERVICES:
            add_service(dep_id)
        elif dep_id.startswith("lib:") or dep_id.startswith("library:"):
            library_assets.append({"id": dep_id.split(":", 1)[1]})
        else:
            # Unknown dependency ids are treated as skill dependencies by default.
            add_skill(dep_id)

    for item in _as_list(frontmatter.get("tools")):
        tool_id = _normalize_id(item)
        if tool_id:
            add_tool(tool_id)

    tooling = frontmatter.get("tooling")
    if isinstance(tooling, dict):
        for item in _as_list(tooling.get("required_tools")):
            tool_id = _normalize_id(item)
            if tool_id:
                add_tool(tool_id)

    for perm in _as_list(frontmatter.get("permissions")):
        if not isinstance(perm, str):
            continue
        mapped = PERMISSION_TO_CAPABILITY.get(perm.strip())
        if mapped:
            add_cap(mapped)

    engine = frontmatter.get("engine")
    if isinstance(engine, dict):
        for key in ("min_reasoning_tier", "preferred_model", "context_required", "min_adapter_version"):
            if key in engine and engine[key] is not None:
                runtime_requirements.append({"key": key, "value": engine[key]})

    return {
        "schema_version": "0.1",
        "skill_dependencies": skill_dependencies,
        "packaged_tools": packaged_tools,
        "host_capabilities": host_capabilities,
        "external_services": external_services,
        "library_assets": library_assets,
        "runtime_requirements": runtime_requirements,
        "optional_dependencies": optional_dependencies,
        "certified_alternatives": [],
    }


def migrate_legacy_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """Return a partial Skill Pack-shaped mapping derived from legacy frontmatter."""
    dependencies = migrate_dependencies(frontmatter)
    skill_id = str(frontmatter.get("name") or frontmatter.get("skill_id") or "").strip()
    return {
        "schema_version": "0.1",
        "skill_id": skill_id,
        "display_name": str(frontmatter.get("display_name") or skill_id),
        "version": str(frontmatter.get("version") or "0.0.0"),
        "description": str(frontmatter.get("description") or ""),
        "format_profile": frontmatter.get("format_profile") or "simple",
        "routing": {
            "when_to_use": str(frontmatter.get("usage_trigger") or ""),
            "when_not_to_use": [str(x) for x in _as_list(frontmatter.get("scope_out"))],
            "tags": [str(x) for x in _as_list(frontmatter.get("tags"))],
        },
        "dependencies": dependencies,
    }
