"""Compatibility wrappers for lib.skill_runtime → Gateway migration.

When ``GATEWAY_URL`` is set, ``load_skill`` / ``record_invocation`` style calls
route through the HTTP gateway. Otherwise they fall back to the existing
``lib.skill_runtime`` implementation so current Python consumers keep working.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .client import SkillsGatewayClient
from .paci_token_client import AUTH_MODE_LOCAL_TEST, resolve_auth_mode


def _gateway_url() -> Optional[str]:
    value = (os.environ.get("GATEWAY_URL") or "").strip()
    return value or None


def _client_from_env_or_static(
    *,
    authorization: Optional[str] = None,
) -> SkillsGatewayClient:
    """Prefer PACI ``from_env``; fall back to explicit/local-test static bearer."""
    if authorization:
        return SkillsGatewayClient(
            base_url=_gateway_url(),
            authorization=authorization,
        )
    try:
        return SkillsGatewayClient.from_env()
    except Exception:
        # Preserve prior local/dev behavior when PACI env is absent and a
        # static GATEWAY_TOKEN is injected under local-test, or when callers
        # still pass an explicit client.
        static = os.environ.get("GATEWAY_TOKEN")
        if static and resolve_auth_mode() == AUTH_MODE_LOCAL_TEST:
            return SkillsGatewayClient(
                base_url=_gateway_url(),
                authorization=static,
            )
        if static:
            # Explicit constructor injection path for existing unit tests that
            # set GATEWAY_TOKEN without flipping AUTH_MODE — still construct,
            # but production canary must use PACI / local-test mode.
            return SkillsGatewayClient(
                base_url=_gateway_url(),
                authorization=static,
            )
        raise


def load_skill(
    skill_id: str,
    *,
    repo_root: Optional[Path] = None,
    require_usable: bool = False,
    authorization: Optional[str] = None,
    client: Optional[SkillsGatewayClient] = None,
) -> Any:
    """Load skill metadata/bundle via Gateway when configured, else lib.skill_runtime."""
    if _gateway_url():
        gw = client or _client_from_env_or_static(authorization=authorization)
        describe = gw.call("skills_describe", {"skill_id": skill_id})
        data = describe.get("data") or {}
        if require_usable and data.get("certification_state") != "usable":
            raise PermissionError(
                f"Skill '{skill_id}' certification_state is "
                f"'{data.get('certification_state')}', not 'usable'."
            )
        # Progressive disclosure starts at level 2 (summary) unless caller goes deeper.
        fragment = gw.call(
            "skills_fragment_get",
            {"skill_id": skill_id, "disclosure_level": 2},
        )
        return {
            "source": "gateway",
            "skill_id": skill_id,
            "describe": data,
            "fragment": (fragment.get("data") or {}),
            "envelope": describe,
        }

    from lib.skill_runtime import load_skill as _load_skill

    return _load_skill(skill_id, repo_root=repo_root, require_usable=require_usable)


def record_invocation(
    event: Any,
    *,
    repo_root: Optional[Path] = None,
    authorization: Optional[str] = None,
    client: Optional[SkillsGatewayClient] = None,
    write_supabase: bool = True,
) -> Dict[str, Any]:
    """Record an invocation via Gateway feedback/run path or local skill_runtime."""
    if _gateway_url():
        gw = client or _client_from_env_or_static(authorization=authorization)
        if hasattr(event, "to_ledger_dict"):
            raw = event.to_ledger_dict()
        elif isinstance(event, Mapping):
            raw = dict(event)
        else:
            raw = {
                "skill": getattr(event, "skill", None),
                "status": getattr(event, "status", None),
                "summary": getattr(event, "summary", None),
            }
        # Always buffer/submit the mapped skills_feedback_submit shape — never
        # the legacy invocation ledger keys (skill/status/summary) alone.
        mapped = {
            "skill_id": raw.get("skill_id") or raw.get("skill"),
            "kind": raw.get("kind") or "invocation",
            "outcome": raw.get("outcome") if "outcome" in raw else raw.get("status"),
            "notes": raw.get("notes") if "notes" in raw else raw.get("summary"),
            "run_id": raw.get("run_id") or raw.get("run_ref"),
        }
        try:
            result = gw.call("skills_feedback_submit", mapped)
            return {"source": "gateway", "result": result}
        except Exception as exc:  # noqa: BLE001 — buffer offline
            buffered = gw.buffer_event("skills_feedback_submit", mapped)
            return {
                "source": "gateway_buffered",
                "event_id": buffered.event_id,
                "error": str(exc),
            }

    from lib.skill_runtime import record_invocation as _record_invocation

    return _record_invocation(
        event,
        repo_root=repo_root,
        write_supabase=write_supabase,
    )
