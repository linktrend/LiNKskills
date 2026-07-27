"""In-memory + catalog-backed Skills Gateway domain service.

Implements plan §13 operations. Ordinary consumers see published/immutable
release metadata from the catalog index (and in-memory overlays). No business
logic is duplicated in MCP or HTTP layers — both call this service.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .auth import ActorClaims


CONTRACT_VERSION = "skills.api.v0.1"

OPERATIONS: Tuple[str, ...] = (
    "skills_list",
    "skills_search",
    "skills_describe",
    "skills_fragment_get",
    "skills_release_get",
    "skills_run_start",
    "skills_run_update",
    "skills_run_complete",
    "skills_run_fail",
    "skills_tool_resolve",
    "skills_tool_invoke",
    "skills_input_validate",
    "skills_output_validate",
    "skills_feedback_submit",
    "skills_trace_candidate_submit",
)

WRITE_OPERATIONS = frozenset(
    {
        "skills_run_start",
        "skills_run_update",
        "skills_run_complete",
        "skills_run_fail",
        "skills_tool_invoke",
        "skills_feedback_submit",
        "skills_trace_candidate_submit",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root_from_here() -> Path:
    # packages/gateway/linkskills_gateway/service.py -> repo root
    return Path(__file__).resolve().parents[3]


@dataclass
class SkillRecord:
    skill_id: str
    version: str
    path: str
    description: str
    format_profile: str
    eval_suite_ref: str
    certification_state: str
    min_reasoning_tier: Optional[str] = None
    usage_trigger: Optional[str] = None
    category: str = "general"
    release_hash: str = ""
    profile_hash: str = ""
    fragments: Dict[str, str] = field(default_factory=dict)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    def to_list_item(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "description": self.description,
            "format_profile": self.format_profile,
            "certification_state": self.certification_state,
            "category": self.category,
            "usage_trigger": self.usage_trigger,
            "release_hash": self.release_hash,
            "profile_hash": self.profile_hash,
        }


@dataclass
class SkillRun:
    run_id: str
    skill_id: str
    version: str
    release_hash: str
    profile_hash: str
    actor_id: str
    org_id: str
    status: str
    created_at: str
    updated_at: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    feedback: List[Dict[str, Any]] = field(default_factory=list)
    outcome: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None


class ServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        http_status: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.http_status = http_status


class SkillsGatewayService:
    """Catalog + in-memory run/telemetry operations for Gateway and MCP."""

    def __init__(
        self,
        *,
        repo_root: Optional[Path] = None,
        catalog_index: Optional[Mapping[str, Any]] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root else _repo_root_from_here()
        self._clock = clock or time.time
        self._skills: Dict[str, SkillRecord] = {}
        self._runs: Dict[str, SkillRun] = {}
        self._idempotency: Dict[str, Dict[str, Any]] = {}
        self._feedback: List[Dict[str, Any]] = []
        self._trace_candidates: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []
        self._ready = True
        self._load_catalog(catalog_index)

    # ------------------------------------------------------------------ load
    def _load_catalog(self, catalog_index: Optional[Mapping[str, Any]]) -> None:
        if catalog_index is None:
            index_path = self.repo_root / "catalog" / "index.json"
            if index_path.is_file():
                catalog_index = json.loads(index_path.read_text(encoding="utf-8"))
            else:
                catalog_index = {"skills": []}

        for raw in catalog_index.get("skills", []):
            skill_id = str(raw["skill_id"])
            version = str(raw.get("version") or "0.0.0")
            release_hash = self._stable_hash(f"{skill_id}:{version}:release")
            profile_hash = self._stable_hash(f"{skill_id}:{version}:profile")
            category = self._infer_category(skill_id, str(raw.get("description") or ""))
            skill_root = self.repo_root / "skills" / skill_id
            fragments = self._build_level_fragments(
                skill_id=skill_id,
                version=version,
                description=str(raw.get("description") or ""),
                usage_trigger=raw.get("usage_trigger"),
                certification_state=str(raw.get("certification_state") or "draft"),
                format_profile=str(raw.get("format_profile") or "heavy"),
                category=category,
                skill_root=skill_root,
            )
            record = SkillRecord(
                skill_id=skill_id,
                version=version,
                path=str(raw.get("path") or f"skills/{skill_id}"),
                description=str(raw.get("description") or ""),
                format_profile=str(raw.get("format_profile") or "heavy"),
                eval_suite_ref=str(raw.get("eval_suite_ref") or ""),
                certification_state=str(raw.get("certification_state") or "draft"),
                min_reasoning_tier=raw.get("min_reasoning_tier"),
                usage_trigger=raw.get("usage_trigger"),
                category=category,
                release_hash=release_hash,
                profile_hash=profile_hash,
                fragments=fragments,
                tools=[
                    {
                        "tool_id": f"{skill_id}.echo",
                        "version": "1.0.0",
                        "placement": "packaged",
                        "descriptor_hash": self._stable_hash(f"{skill_id}:echo"),
                    }
                ],
                input_schema={"type": "object", "properties": {"task": {"type": "string"}}},
                output_schema={
                    "type": "object",
                    "properties": {"summary": {"type": "string"}},
                },
            )
            self._skills[skill_id] = record

    def _build_level_fragments(
        self,
        *,
        skill_id: str,
        version: str,
        description: str,
        usage_trigger: Optional[str],
        certification_state: str,
        format_profile: str,
        category: str,
        skill_root: Path,
    ) -> Dict[str, str]:
        """Build progressive-disclosure fragments for levels 0–6 from SkillBundle paths."""
        skill_md = skill_root / "SKILL.md"
        skill_text = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else (
            f"# {skill_id}\n\n{description}\n"
        )
        disclosure_paths: Dict[str, Path] = {"SKILL.md": skill_md} if skill_md.is_file() else {}
        for rel in ("advanced", "examples", "references", "scripts"):
            candidate = skill_root / rel
            if candidate.exists():
                disclosure_paths[rel] = candidate

        def _read_tree(path: Path, *, limit: int = 8000) -> str:
            if not path.exists():
                return ""
            if path.is_file():
                return path.read_text(encoding="utf-8")[:limit]
            chunks: List[str] = []
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in {
                    ".md",
                    ".yaml",
                    ".yml",
                    ".json",
                    ".txt",
                }:
                    rel = child.relative_to(path)
                    chunks.append(f"## {rel}\n{child.read_text(encoding='utf-8')[:2000]}\n")
                    if sum(len(c) for c in chunks) >= limit:
                        break
            return "\n".join(chunks)[:limit]

        level0 = json.dumps(
            {
                "skill_id": skill_id,
                "version": version,
                "description": description,
                "category": category,
                "certification_state": certification_state,
                "format_profile": format_profile,
                "disclosure_paths": sorted(disclosure_paths.keys()),
            },
            indent=2,
            sort_keys=True,
        )
        level1 = (
            f"# {skill_id} — routing\n\n"
            f"usage_trigger: {usage_trigger or 'unspecified'}\n"
            f"category: {category}\n"
            f"format_profile: {format_profile}\n"
            f"certification_state: {certification_state}\n\n"
            f"{description}\n"
        )
        level2 = skill_text[:1200]
        level3 = _read_tree(skill_root / "advanced") or skill_text[:4000]
        level4 = _read_tree(skill_root / "references") or (
            f"# Verification / failure for {skill_id}\n"
            "Follow SKILL.md verification steps and fail closed on missing evidence.\n"
        )
        level5 = _read_tree(skill_root / "examples") or (
            f"# Examples / schemas for {skill_id}\n"
            "No examples/ directory present; use input/output schemas from describe.\n"
        )
        full_parts = [skill_text]
        for key, path in sorted(disclosure_paths.items()):
            if key == "SKILL.md":
                continue
            body = _read_tree(path, limit=12000)
            if body:
                full_parts.append(f"\n\n# disclosure:{key}\n{body}")
        level6 = "\n".join(full_parts)

        return {
            "0": level0,
            "1": level1,
            "2": level2,
            "3": level3,
            "4": level4,
            "5": level5,
            "6": level6,
            # Named aliases retained for older callers / recommended_next flows.
            "index": level0,
            "routing": level1,
            "requirements": level2,
            "skill_md_head": level2,
            "procedure": level3,
            "verification": level4,
            "examples": level5,
            "full_pack": level6,
        }

    @staticmethod
    def _stable_hash(material: str) -> str:
        return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _infer_category(skill_id: str, description: str) -> str:
        text = f"{skill_id} {description}".lower()
        if any(k in text for k in ("git", "branch", "commit", "pr")):
            return "git"
        if any(k in text for k in ("test", "eval", "qa")):
            return "quality"
        if any(k in text for k in ("doc", "brief", "handoff")):
            return "docs"
        if any(k in text for k in ("security", "audit", "secret")):
            return "security"
        return "general"

    # ---------------------------------------------------------------- envelope
    def envelope(
        self,
        *,
        actor: Optional[ActorClaims],
        operation: str,
        request_id: str,
        idempotency_id: Optional[str],
        data: Any = None,
        warnings: Optional[List[str]] = None,
        recommended_next: Optional[str] = None,
        error: Optional[Mapping[str, Any]] = None,
        release_hash: Optional[str] = None,
        profile_hash: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "operation": operation,
            "request_id": request_id,
            "idempotency_id": idempotency_id,
            "server_time": _utc_now(),
            "actor_id": actor.actor_id if actor else None,
            "org_id": actor.org_id if actor else None,
            "run_id": run_id,
            "release_hash": release_hash,
            "execution_profile_hash": profile_hash,
            "data": data,
            "warnings": list(warnings or []),
            "compatibility": {"state": "stable", "deprecation": None},
            "recommended_next": recommended_next,
            "error": dict(error) if error else None,
        }

    # ---------------------------------------------------------------- dispatch
    def dispatch(
        self,
        operation: str,
        params: Optional[Mapping[str, Any]],
        *,
        actor: ActorClaims,
        request_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        if operation not in OPERATIONS:
            raise ServiceError("unknown_operation", f"Unknown operation: {operation}", http_status=404)

        params = dict(params or {})
        request_id = request_id or str(uuid.uuid4())
        idempotency_key = idempotency_key or params.pop("idempotency_key", None)

        if operation in WRITE_OPERATIONS and not (
            actor.has_scope("skills:write") or actor.has_scope("*")
        ):
            # Allow run lifecycle with skills:run as a narrower write scope.
            if operation.startswith("skills_run_") and actor.has_scope("skills:run"):
                pass
            elif operation in {"skills_feedback_submit", "skills_trace_candidate_submit"} and (
                actor.has_scope("skills:feedback") or actor.has_scope("skills:run")
            ):
                pass
            else:
                raise ServiceError(
                    "auth_forbidden",
                    f"Scope insufficient for {operation}",
                    http_status=403,
                )

        if operation == "skills_run_start" and idempotency_key:
            cache_key = f"{actor.actor_id}:{operation}:{idempotency_key}"
            cached = self._idempotency.get(cache_key)
            if cached is not None:
                # Return prior envelope with fresh request/server metadata.
                replay = dict(cached)
                replay["request_id"] = request_id
                replay["server_time"] = _utc_now()
                replay["warnings"] = list(replay.get("warnings") or []) + [
                    "idempotent_replay"
                ]
                return replay

        handler = getattr(self, f"op_{operation}")
        result = handler(actor=actor, params=params, idempotency_key=idempotency_key)
        env = self.envelope(
            actor=actor,
            operation=operation,
            request_id=request_id,
            idempotency_id=idempotency_key,
            data=result.get("data"),
            warnings=result.get("warnings"),
            recommended_next=result.get("recommended_next"),
            release_hash=result.get("release_hash"),
            profile_hash=result.get("profile_hash"),
            run_id=result.get("run_id"),
        )

        if operation == "skills_run_start" and idempotency_key:
            cache_key = f"{actor.actor_id}:{operation}:{idempotency_key}"
            self._idempotency[cache_key] = dict(env)
        return env

    # -------------------------------------------------------------- helpers
    def _get_skill(self, skill_id: str) -> SkillRecord:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ServiceError("not_found", f"Unknown skill_id: {skill_id}", http_status=404)
        return skill

    def _get_run(self, run_id: str, actor: ActorClaims) -> SkillRun:
        run = self._runs.get(run_id)
        if not run:
            raise ServiceError("not_found", f"Unknown run_id: {run_id}", http_status=404)
        if run.actor_id != actor.actor_id or run.org_id != actor.org_id:
            raise ServiceError(
                "auth_forbidden",
                "Run belongs to another actor/org",
                http_status=403,
            )
        return run

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "linkskills-gateway",
            "contract_version": CONTRACT_VERSION,
            "skill_count": len(self._skills),
            "time": _utc_now(),
        }

    def ready(self) -> Dict[str, Any]:
        return {
            "ready": self._ready and len(self._skills) > 0,
            "catalog_loaded": len(self._skills) > 0,
            "time": _utc_now(),
        }

    # ----------------------------------------------------------- operations
    def op_skills_list(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        usable_only = bool(params.get("usable_only", False))
        category = params.get("category")
        include_states = params.get("include_states")
        allowed = None
        if usable_only:
            allowed = {"usable"}
        elif include_states is not None:
            allowed = set(include_states)

        items = []
        categories: Dict[str, int] = {}
        for skill in sorted(self._skills.values(), key=lambda s: s.skill_id):
            if allowed is not None and skill.certification_state not in allowed:
                continue
            if category and skill.category != category:
                continue
            items.append(skill.to_list_item())
            categories[skill.category] = categories.get(skill.category, 0) + 1

        return {
            "data": {
                "skills": items,
                "categories": categories,
                "count": len(items),
            },
            "recommended_next": "skills_search" if items else "skills_list",
            "warnings": []
            if any(s["certification_state"] == "usable" for s in items)
            else ["no_usable_skills_in_result"],
        }

    def op_skills_search(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        query = str(params.get("query") or params.get("task") or "").strip().lower()
        runtime = str(params.get("runtime") or "").strip().lower()
        limit = int(params.get("limit") or 10)
        ranked: List[Tuple[float, SkillRecord]] = []
        for skill in self._skills.values():
            hay = " ".join(
                [
                    skill.skill_id,
                    skill.description,
                    skill.usage_trigger or "",
                    skill.category,
                ]
            ).lower()
            score = 0.0
            if query:
                for token in re.findall(r"[a-z0-9\-]+", query):
                    if token in hay:
                        score += 1.0
                    if token == skill.skill_id:
                        score += 3.0
            else:
                score = 0.1
            if runtime and runtime in (skill.format_profile, skill.min_reasoning_tier or ""):
                score += 0.5
            if skill.certification_state == "usable":
                score += 1.0
            if score > 0:
                ranked.append((score, skill))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].skill_id))
        results = [
            {**skill.to_list_item(), "score": score}
            for score, skill in ranked[: max(1, limit)]
        ]
        return {
            "data": {"results": results, "query": query, "count": len(results)},
            "recommended_next": "skills_describe" if results else None,
        }

    def op_skills_describe(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        named = sorted(
            k
            for k in skill.fragments
            if k not in {"full_pack", "6"} and not k.isdigit()
        )
        return {
            "data": {
                **skill.to_list_item(),
                "eval_suite_ref": skill.eval_suite_ref,
                "path": skill.path,
                "min_reasoning_tier": skill.min_reasoning_tier,
                "breadcrumbs": ["skills_list", "skills_search", "skills_describe"],
                "available_fragments": named,
                "disclosure_levels": list(range(0, 7)),
                "tools": skill.tools,
            },
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
            "recommended_next": "skills_fragment_get",
        }

    def op_skills_fragment_get(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        level_raw = params.get("disclosure_level", params.get("level"))
        fragment_id = params.get("fragment_id")
        explicit_full = bool(params.get("explicit_full_pack"))

        if level_raw is not None:
            try:
                level = int(level_raw)
            except (TypeError, ValueError) as exc:
                raise ServiceError(
                    "invalid_level",
                    "disclosure_level must be an integer 0-6",
                ) from exc
            if level < 0 or level > 6:
                raise ServiceError(
                    "invalid_level",
                    "disclosure_level must be between 0 and 6",
                )
            fragment_id = str(level)
        else:
            fragment_id = str(fragment_id or "routing")

        if fragment_id in {"full_pack", "6"} and not explicit_full:
            raise ServiceError(
                "full_pack_requires_explicit",
                "full_pack / level 6 requires explicit_full_pack=true",
            )
        if fragment_id not in skill.fragments:
            raise ServiceError(
                "not_found",
                f"Unknown fragment_id: {fragment_id}",
                http_status=404,
            )
        content = skill.fragments[fragment_id]
        disclosure_level = (
            int(fragment_id)
            if fragment_id.isdigit()
            else {
                "index": 0,
                "routing": 1,
                "requirements": 2,
                "skill_md_head": 2,
                "procedure": 3,
                "verification": 4,
                "examples": 5,
                "full_pack": 6,
            }.get(fragment_id, 1)
        )
        self._events.append(
            {
                "type": "fragment_disclosure",
                "skill_id": skill.skill_id,
                "fragment_id": fragment_id,
                "disclosure_level": disclosure_level,
                "bytes": len(content.encode("utf-8")),
                "at": _utc_now(),
            }
        )
        return {
            "data": {
                "skill_id": skill.skill_id,
                "fragment_id": fragment_id,
                "disclosure_level": disclosure_level,
                "content": content,
                "content_hash": self._stable_hash(content),
            },
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
            "recommended_next": "skills_run_start",
        }

    def op_skills_release_get(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        return {
            "data": {
                "skill_id": skill.skill_id,
                "version": skill.version,
                "release_hash": skill.release_hash,
                "profile_hash": skill.profile_hash,
                "certification_state": skill.certification_state,
                "immutable": True,
                "eval_suite_ref": skill.eval_suite_ref,
            },
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
        }

    def op_skills_run_start(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        skill = self._get_skill(str(params.get("skill_id") or ""))
        version = str(params.get("version") or skill.version)
        if version != skill.version:
            raise ServiceError(
                "version_mismatch",
                f"Requested version {version} != published {skill.version}",
            )
        now = _utc_now()
        run_id = str(uuid.uuid4())
        run = SkillRun(
            run_id=run_id,
            skill_id=skill.skill_id,
            version=skill.version,
            release_hash=skill.release_hash,
            profile_hash=skill.profile_hash,
            actor_id=actor.actor_id,
            org_id=actor.org_id,
            status="started",
            created_at=now,
            updated_at=now,
            events=[{"type": "run_started", "at": now}],
            idempotency_key=idempotency_key,
        )
        self._runs[run_id] = run
        self._events.append(
            {
                "type": "run_started",
                "run_id": run_id,
                "skill_id": skill.skill_id,
                "actor_id": actor.actor_id,
                "at": now,
            }
        )
        return {
            "data": {
                "run_id": run_id,
                "skill_id": skill.skill_id,
                "version": skill.version,
                "status": run.status,
                "starting_fragments": ["routing", "requirements"],
            },
            "run_id": run_id,
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
            "recommended_next": "skills_run_update",
        }

    def op_skills_run_update(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del idempotency_key
        run = self._get_run(str(params.get("run_id") or ""), actor)
        if run.status in {"completed", "failed"}:
            raise ServiceError("run_closed", f"Run already {run.status}")
        event = {
            "type": "run_update",
            "at": _utc_now(),
            "progress": params.get("progress"),
            "disclosure": params.get("disclosure"),
            "validation": params.get("validation"),
            "artifact_refs": params.get("artifact_refs") or [],
        }
        run.events.append(event)
        run.updated_at = event["at"]
        run.status = "in_progress"
        return {
            "data": {"run_id": run.run_id, "status": run.status, "event": event},
            "run_id": run.run_id,
            "release_hash": run.release_hash,
            "profile_hash": run.profile_hash,
            "recommended_next": "skills_run_complete",
        }

    def op_skills_run_complete(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del idempotency_key
        run = self._get_run(str(params.get("run_id") or ""), actor)
        if run.status in {"completed", "failed"}:
            raise ServiceError("run_closed", f"Run already {run.status}")
        now = _utc_now()
        outcome = {
            "classification": params.get("classification") or "success",
            "output": params.get("output"),
            "evidence": params.get("evidence") or {},
            "feedback": params.get("feedback"),
            "closed_at": now,
        }
        run.outcome = outcome
        run.status = "completed"
        run.updated_at = now
        run.events.append({"type": "run_completed", "at": now, "outcome": outcome})
        return {
            "data": {"run_id": run.run_id, "status": run.status, "outcome": outcome},
            "run_id": run.run_id,
            "release_hash": run.release_hash,
            "profile_hash": run.profile_hash,
            "recommended_next": "skills_feedback_submit",
        }

    def op_skills_run_fail(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del idempotency_key
        run = self._get_run(str(params.get("run_id") or ""), actor)
        if run.status in {"completed", "failed"}:
            raise ServiceError("run_closed", f"Run already {run.status}")
        now = _utc_now()
        failure = {
            "error_class": params.get("error_class") or "unspecified",
            "message": params.get("message") or "run failed",
            "trace_to_eval_eligible": bool(params.get("trace_to_eval_eligible", True)),
            "details": params.get("details") or {},
            "closed_at": now,
        }
        run.outcome = failure
        run.status = "failed"
        run.updated_at = now
        run.events.append({"type": "run_failed", "at": now, "failure": failure})
        return {
            "data": {"run_id": run.run_id, "status": run.status, "failure": failure},
            "run_id": run.run_id,
            "release_hash": run.release_hash,
            "profile_hash": run.profile_hash,
            "recommended_next": "skills_trace_candidate_submit"
            if failure["trace_to_eval_eligible"]
            else None,
        }

    def op_skills_tool_resolve(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        tool_id = params.get("tool_id")
        tools = skill.tools
        if tool_id:
            tools = [t for t in tools if t["tool_id"] == tool_id]
            if not tools:
                raise ServiceError("not_found", f"Unknown tool_id: {tool_id}", http_status=404)
        return {
            "data": {"skill_id": skill.skill_id, "tools": tools},
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
            "recommended_next": "skills_tool_invoke",
        }

    def op_skills_tool_invoke(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        tool_id = str(params.get("tool_id") or "")
        tool = next((t for t in skill.tools if t["tool_id"] == tool_id), None)
        if not tool:
            raise ServiceError("not_found", f"Unknown tool_id: {tool_id}", http_status=404)
        payload = params.get("input") or {}
        # Dry-run is the default; live side effects require dry_run=false.
        dry_run = True if "dry_run" not in params else bool(params.get("dry_run"))
        result = {
            "tool_id": tool_id,
            "version": tool["version"],
            "descriptor_hash": tool["descriptor_hash"],
            "dry_run": dry_run,
            "output": {
                "echo": payload,
                "invoked_by": actor.actor_id,
                "mode": "dry_run" if dry_run else "live_echo",
            },
            "side_effects": "none",
        }
        self._events.append(
            {
                "type": "tool_invocation",
                "tool_id": tool_id,
                "actor_id": actor.actor_id,
                "dry_run": dry_run,
                "at": _utc_now(),
            }
        )
        warnings = ["tool_invoke_dry_run"] if dry_run else []
        return {
            "data": result,
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
            "warnings": warnings,
        }

    def op_skills_input_validate(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        payload = params.get("input")
        ok = isinstance(payload, Mapping)
        errors: List[str] = []
        if not ok:
            errors.append("input must be an object")
        elif "task" in skill.input_schema.get("properties", {}) and "task" not in payload:
            # Soft contract check for v0.1
            errors.append("missing recommended field: task")
            ok = False
        return {
            "data": {"valid": ok and not errors, "errors": errors, "schema": skill.input_schema},
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
        }

    def op_skills_output_validate(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del actor, idempotency_key
        skill = self._get_skill(str(params.get("skill_id") or ""))
        payload = params.get("output")
        errors: List[str] = []
        ok = isinstance(payload, Mapping)
        if not ok:
            errors.append("output must be an object")
        elif "summary" not in (payload or {}):
            errors.append("missing field: summary")
            ok = False
        return {
            "data": {
                "valid": bool(ok and not errors),
                "errors": errors,
                "schema": skill.output_schema,
            },
            "release_hash": skill.release_hash,
            "profile_hash": skill.profile_hash,
        }

    def op_skills_feedback_submit(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del idempotency_key
        record = {
            "feedback_id": str(uuid.uuid4()),
            "actor_id": actor.actor_id,
            "org_id": actor.org_id,
            "skill_id": params.get("skill_id"),
            "run_id": params.get("run_id"),
            "kind": params.get("kind") or "correction",
            "rating": params.get("rating"),
            "friction": params.get("friction"),
            "missing_step": params.get("missing_step"),
            "outcome": params.get("outcome"),
            "notes": params.get("notes"),
            "at": _utc_now(),
        }
        self._feedback.append(record)
        if record.get("run_id") and record["run_id"] in self._runs:
            self._runs[str(record["run_id"])].feedback.append(record)
        return {
            "data": record,
            "recommended_next": None,
        }

    def op_skills_trace_candidate_submit(
        self,
        *,
        actor: ActorClaims,
        params: Mapping[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, Any]:
        del idempotency_key
        # Deduplicate by (skill_id, run_id, fingerprint)
        fingerprint = str(
            params.get("fingerprint")
            or self._stable_hash(
                json.dumps(
                    {
                        "skill_id": params.get("skill_id"),
                        "run_id": params.get("run_id"),
                        "summary": params.get("summary"),
                    },
                    sort_keys=True,
                )
            )
        )
        for existing in self._trace_candidates:
            if existing.get("fingerprint") == fingerprint:
                return {
                    "data": {**existing, "deduplicated": True},
                    "warnings": ["duplicate_trace_candidate"],
                }
        record = {
            "candidate_id": str(uuid.uuid4()),
            "fingerprint": fingerprint,
            "actor_id": actor.actor_id,
            "org_id": actor.org_id,
            "skill_id": params.get("skill_id"),
            "run_id": params.get("run_id"),
            "summary": params.get("summary"),
            "observed": params.get("observed") or {},
            "status": "queued",
            "at": _utc_now(),
            "deduplicated": False,
        }
        self._trace_candidates.append(record)
        return {"data": record, "recommended_next": "enqueue_review"}
