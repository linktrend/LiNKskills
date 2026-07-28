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
from .persistence import (
    GatewayStore,
    InMemoryGatewayStore,
    canonical_request_hash,
    open_gateway_store,
    resolve_state_dir,
)

try:
    from linkskills_core.payload_guard import (
        PayloadValidationError,
        prepare_feedback_params,
        prepare_run_mutation_params,
        prepare_trace_params,
    )
except ImportError:  # pragma: no cover - path wiring in tests
    PayloadValidationError = None  # type: ignore[misc, assignment]
    prepare_feedback_params = None  # type: ignore[misc, assignment]
    prepare_run_mutation_params = None  # type: ignore[misc, assignment]
    prepare_trace_params = None  # type: ignore[misc, assignment]


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

# Mutations owned by the gateway store — reservation+mutation+completion are atomic.
DB_OWNED_WRITE_OPERATIONS = frozenset(
    {
        "skills_run_start",
        "skills_run_update",
        "skills_run_complete",
        "skills_run_fail",
        "skills_feedback_submit",
        "skills_trace_candidate_submit",
    }
)

# External side effects — fence + durable intent/result; at-least-once with downstream key.
EXTERNAL_SIDE_EFFECT_OPERATIONS = frozenset({"skills_tool_invoke"})


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
    compatible_runtime_profiles: List[str] = field(default_factory=list)
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
        state_dir: Optional[Path] = None,
        store: Optional[GatewayStore] = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root else _repo_root_from_here()
        self._clock = clock or time.time
        self._state_dir = resolve_state_dir(repo_root=self.repo_root, state_dir=state_dir)
        self._store = open_gateway_store(
            repo_root=self.repo_root,
            state_dir=state_dir,
            store=store,
        )
        self._durable = not isinstance(self._store, InMemoryGatewayStore)
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
            compatible_profiles = raw.get("compatible_runtime_profiles") or raw.get(
                "runtime_profile_tags"
            ) or []
            if isinstance(compatible_profiles, str):
                compatible_profiles = [compatible_profiles]
            # Allow catalog override of stable hashes when provided (tests / pinned releases).
            if raw.get("release_hash"):
                release_hash = str(raw["release_hash"])
            if raw.get("profile_hash"):
                profile_hash = str(raw["profile_hash"])
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
                compatible_runtime_profiles=[str(p) for p in compatible_profiles],
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

        # Exact permittedOperations enforcement for every read and mutation.
        if not actor.has_scope("lskills") and "*" not in actor.scopes:
            raise ServiceError(
                "auth_forbidden",
                "Missing required service scope: lskills",
                http_status=403,
            )
        if not actor.may_perform(operation):
            raise ServiceError(
                "auth_forbidden",
                f"permittedOperations insufficient for {operation}",
                http_status=403,
            )

        if operation in WRITE_OPERATIONS and idempotency_key:
            request_hash = canonical_request_hash(
                {
                    "actor_id": actor.actor_id,
                    "org_id": actor.org_id,
                    "operation": operation,
                    "params": params,
                }
            )
            if operation in DB_OWNED_WRITE_OPERATIONS:
                handler = getattr(self, f"op_{operation}")

                def mutator() -> Dict[str, Any]:
                    result = handler(
                        actor=actor, params=params, idempotency_key=idempotency_key
                    )
                    return self.envelope(
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

                reserved = self._store.run_atomic_idempotent(
                    actor.actor_id,
                    operation,
                    idempotency_key,
                    request_hash,
                    mutator,
                )
                if reserved.outcome == "conflict":
                    raise ServiceError(
                        "idempotency_conflict",
                        "idempotency key already bound to a different request payload",
                        http_status=409,
                    )
                if reserved.outcome == "in_progress":
                    raise ServiceError(
                        "idempotency_in_progress",
                        "idempotency key is reserved by an in-flight request; retry later",
                        http_status=409,
                    )
                assert reserved.envelope is not None
                env = dict(reserved.envelope)
                env["request_id"] = request_id
                env["server_time"] = _utc_now()
                # Prior completion has no fence; fresh atomic completion includes one.
                if reserved.fence_token is None:
                    env["warnings"] = list(env.get("warnings") or []) + [
                        "idempotent_replay"
                    ]
                return env

            # External side-effect path: fence + durable intent/result reconciliation.
            reserved = self._store.reserve_idempotency(
                actor.actor_id, operation, idempotency_key, request_hash
            )
            if reserved.outcome == "conflict":
                raise ServiceError(
                    "idempotency_conflict",
                    "idempotency key already bound to a different request payload",
                    http_status=409,
                )
            if reserved.outcome == "in_progress":
                raise ServiceError(
                    "idempotency_in_progress",
                    "idempotency key is reserved by an in-flight request; retry later",
                    http_status=409,
                )
            if reserved.outcome == "replay" and reserved.envelope is not None:
                replay = dict(reserved.envelope)
                replay["request_id"] = request_id
                replay["server_time"] = _utc_now()
                replay["warnings"] = list(replay.get("warnings") or []) + [
                    "idempotent_replay"
                ]
                return replay
            assert reserved.fence_token is not None
            fence_token = reserved.fence_token
            downstream_key = f"{actor.actor_id}:{operation}:{idempotency_key}:{fence_token}"
            prior = self._store.get_side_effect_intent(
                actor.actor_id, operation, idempotency_key
            )
            if (
                prior
                and prior.get("status") == "result"
                and prior.get("result") is not None
                and str(prior.get("fence_token") or "") == fence_token
            ):
                env = self.envelope(
                    actor=actor,
                    operation=operation,
                    request_id=request_id,
                    idempotency_id=idempotency_key,
                    data=prior["result"],
                    warnings=["side_effect_reconciled"],
                )
                try:
                    self._store.complete_idempotency(
                        actor.actor_id,
                        operation,
                        idempotency_key,
                        request_hash,
                        dict(env),
                        fence_token=fence_token,
                    )
                except ValueError as exc:
                    raise ServiceError(
                        "idempotency_fence_rejected",
                        str(exc),
                        http_status=409,
                    ) from exc
                return env
            self._store.record_side_effect_intent(
                actor.actor_id,
                operation,
                idempotency_key,
                fence_token=fence_token,
                downstream_key=downstream_key,
                request_hash=request_hash,
            )
            handler = getattr(self, f"op_{operation}")
            try:
                result = handler(
                    actor=actor,
                    params={**params, "downstream_idempotency_key": downstream_key},
                    idempotency_key=idempotency_key,
                )
                env = self.envelope(
                    actor=actor,
                    operation=operation,
                    request_id=request_id,
                    idempotency_id=idempotency_key,
                    data=result.get("data"),
                    warnings=list(result.get("warnings") or [])
                    + ["external_side_effect_at_least_once"],
                    recommended_next=result.get("recommended_next"),
                    release_hash=result.get("release_hash"),
                    profile_hash=result.get("profile_hash"),
                    run_id=result.get("run_id"),
                )
                self._store.complete_side_effect_intent(
                    actor.actor_id,
                    operation,
                    idempotency_key,
                    fence_token=fence_token,
                    result=dict(result.get("data") or {}),
                )
                self._store.complete_idempotency(
                    actor.actor_id,
                    operation,
                    idempotency_key,
                    request_hash,
                    dict(env),
                    fence_token=fence_token,
                )
                return env
            except ServiceError:
                raise
            except ValueError as exc:
                raise ServiceError(
                    "idempotency_fence_rejected",
                    str(exc),
                    http_status=409,
                ) from exc
            except Exception:
                # Leave reservation leased; fence rejects late displaced completion.
                raise

        handler = getattr(self, f"op_{operation}")
        result = handler(actor=actor, params=params, idempotency_key=idempotency_key)
        return self.envelope(
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

    # -------------------------------------------------------------- helpers
    def _get_skill(self, skill_id: str) -> SkillRecord:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ServiceError("not_found", f"Unknown skill_id: {skill_id}", http_status=404)
        return skill

    def _get_run(self, run_id: str, actor: ActorClaims) -> SkillRun:
        if run_id in self._runs:
            run = self._runs[run_id]
        else:
            stored = self._store.get_run(run_id)
            if stored is None:
                raise ServiceError("not_found", f"Unknown run_id: {run_id}", http_status=404)
            run = SkillRun(
                run_id=str(stored["run_id"]),
                skill_id=str(stored["skill_id"]),
                version=str(stored["version"]),
                release_hash=str(stored.get("release_hash") or ""),
                profile_hash=str(stored.get("profile_hash") or ""),
                actor_id=str(stored["actor_id"]),
                org_id=str(stored["org_id"]),
                status=str(stored["status"]),
                created_at=str(stored["created_at"]),
                updated_at=str(stored["updated_at"]),
                events=list(stored.get("events") or []),
                feedback=list(stored.get("feedback") or []),
                outcome=stored.get("outcome"),
                idempotency_key=stored.get("idempotency_key"),
            )
            self._runs[run_id] = run
        if run.actor_id != actor.actor_id or (run.org_id or "") != (actor.org_id or ""):
            raise ServiceError(
                "auth_forbidden",
                "Run belongs to another actor/org",
                http_status=403,
            )
        return run

    def _guard_params(self, preparer: Any, params: Mapping[str, Any]) -> Dict[str, Any]:
        if preparer is None:
            return dict(params)
        try:
            return preparer(params)
        except PayloadValidationError as exc:  # type: ignore[misc]
            raise ServiceError(exc.code, exc.message, http_status=400) from exc
        except Exception as exc:
            if PayloadValidationError is not None and isinstance(exc, PayloadValidationError):
                raise ServiceError(exc.code, exc.message, http_status=400) from exc
            raise

    def _persist_run(self, run: SkillRun) -> None:
        self._runs[run.run_id] = run
        self._store.save_run(run)

    def _assert_skill_runnable(
        self,
        skill: SkillRecord,
        params: Mapping[str, Any],
    ) -> None:
        """Reject draft / uncertified / hash-mismatched / incompatible-profile starts."""
        state = (skill.certification_state or "").strip()
        if state != "usable":
            raise ServiceError(
                "skill_not_runnable",
                (
                    f"Skill {skill.skill_id!r} certification_state={state!r} "
                    "is not usable (draft/uncertified skills cannot start runs)"
                ),
                http_status=409,
            )

        requested_release = params.get("release_hash") or params.get("skill_release_hash")
        if requested_release is not None and str(requested_release) != skill.release_hash:
            raise ServiceError(
                "release_hash_mismatch",
                (
                    f"Requested release_hash {requested_release!r} != "
                    f"published {skill.release_hash!r}"
                ),
                http_status=409,
            )

        requested_profile = params.get("profile_hash") or params.get("execution_profile_hash")
        if requested_profile is not None and str(requested_profile) != skill.profile_hash:
            raise ServiceError(
                "profile_hash_mismatch",
                (
                    f"Requested profile_hash {requested_profile!r} != "
                    f"published {skill.profile_hash!r}"
                ),
                http_status=409,
            )

        runtime_tags = (
            params.get("runtime_profile_tags")
            or params.get("compatible_runtime_profiles")
            or params.get("execution_profile")
        )
        if runtime_tags is None:
            return
        if isinstance(runtime_tags, str):
            wanted = {runtime_tags}
        elif isinstance(runtime_tags, Mapping):
            wanted = {str(v) for v in runtime_tags.values() if v is not None}
        else:
            wanted = {str(v) for v in runtime_tags if v is not None}
        declared = set(skill.compatible_runtime_profiles)
        if not declared:
            raise ServiceError(
                "profile_incompatible",
                (
                    f"Skill {skill.skill_id!r} declares no compatible runtime profiles "
                    "(fail closed)"
                ),
                http_status=409,
            )
        if declared & {"*", "any"}:
            return
        if not (declared & wanted):
            raise ServiceError(
                "profile_incompatible",
                (
                    f"Skill {skill.skill_id!r} profiles {sorted(declared)} "
                    f"incompatible with requested {sorted(wanted)}"
                ),
                http_status=409,
            )

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
        self._assert_skill_runnable(skill, params)
        now = _utc_now()
        run_id = str(uuid.uuid4())
        run = SkillRun(
            run_id=run_id,
            skill_id=skill.skill_id,
            version=skill.version,
            release_hash=skill.release_hash,
            profile_hash=skill.profile_hash,
            actor_id=actor.actor_id,
            org_id=actor.org_id or "",
            status="started",
            created_at=now,
            updated_at=now,
            events=[{"type": "run_started", "at": now}],
            idempotency_key=idempotency_key,
        )
        self._runs[run_id] = run
        self._persist_run(run)
        self._store.append_event(
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
        clean = self._guard_params(prepare_run_mutation_params, params)
        run = self._get_run(str(clean.get("run_id") or ""), actor)
        if run.status in {"completed", "failed"}:
            raise ServiceError("run_closed", f"Run already {run.status}")
        event = {
            "type": "run_update",
            "at": _utc_now(),
            "progress": clean.get("progress"),
            "disclosure": clean.get("disclosure"),
            "validation": clean.get("validation"),
            "artifact_refs": clean.get("artifact_refs") or [],
        }
        run.events.append(event)
        run.updated_at = event["at"]
        run.status = "in_progress"
        self._persist_run(run)
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
        clean = self._guard_params(prepare_run_mutation_params, params)
        run = self._get_run(str(clean.get("run_id") or ""), actor)
        if run.status in {"completed", "failed"}:
            raise ServiceError("run_closed", f"Run already {run.status}")
        now = _utc_now()
        outcome = {
            "classification": clean.get("classification") or "success",
            "output": clean.get("output"),
            "evidence": clean.get("evidence") or {},
            "feedback": clean.get("feedback"),
            "closed_at": now,
        }
        run.outcome = outcome
        run.status = "completed"
        run.updated_at = now
        run.events.append({"type": "run_completed", "at": now, "outcome": outcome})
        self._persist_run(run)
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
        clean = self._guard_params(prepare_run_mutation_params, params)
        run = self._get_run(str(clean.get("run_id") or ""), actor)
        if run.status in {"completed", "failed"}:
            raise ServiceError("run_closed", f"Run already {run.status}")
        now = _utc_now()
        failure = {
            "error_class": clean.get("error_class") or "unspecified",
            "message": clean.get("message") or "run failed",
            "trace_to_eval_eligible": bool(clean.get("trace_to_eval_eligible", True)),
            "details": clean.get("details") or {},
            "closed_at": now,
        }
        run.outcome = failure
        run.status = "failed"
        run.updated_at = now
        run.events.append({"type": "run_failed", "at": now, "failure": failure})
        self._persist_run(run)
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
        tool_id = str(params.get("tool_id") or "").strip()
        if not tool_id:
            raise ServiceError("invalid_argument", "tool_id is required", http_status=400)

        # Prefer packaged tools under tools/<id>; skill catalog bindings are advisory.
        skill_id = str(params.get("skill_id") or "").strip()
        skill = self._get_skill(skill_id) if skill_id else None
        tool_dir = self.repo_root / "tools" / tool_id
        if not tool_dir.is_dir():
            raise ServiceError("not_found", f"Unknown packaged tool_id: {tool_id}", http_status=404)

        dry_run = True if "dry_run" not in params else bool(params.get("dry_run"))
        version = params.get("version")
        tool_hash = params.get("tool_hash") or params.get("bundle_hash") or params.get("source_hash")
        argv = params.get("argv") or []
        if not isinstance(argv, list):
            raise ServiceError("invalid_argument", "argv must be a list", http_status=400)
        stdin = params.get("stdin")
        if stdin is not None:
            stdin = str(stdin)
        input_payload = params.get("input")

        try:
            from linkskills_tool_runtime.descriptor import load_tool_descriptor
            from linkskills_tool_runtime.invoke import invoke_tool
            from linkskills_tool_runtime.resolve import ResolutionError, resolve_tool
        except ImportError as exc:
            raise ServiceError(
                "tool_runtime_unavailable",
                f"tool runtime import failed: {exc}",
                http_status=500,
            ) from exc

        try:
            if dry_run:
                resolved = resolve_tool(
                    tool_dir,
                    tool_id=tool_id,
                    version=str(version) if version is not None else None,
                    bundle_hash=str(tool_hash) if params.get("bundle_hash") is not None else None,
                    source_hash=str(tool_hash)
                    if params.get("source_hash") is not None and params.get("bundle_hash") is None
                    else None,
                )
                result = {
                    "tool_id": resolved.tool_id,
                    "version": resolved.version,
                    "descriptor_hash": resolved.descriptor.source_hash,
                    "source_hash": resolved.descriptor.source_hash,
                    "bundle_hash": resolved.bundle_hash,
                    "dry_run": True,
                    "output": {
                        "resolved": True,
                        "argv": argv,
                        "input": input_payload,
                        "invoked_by": actor.actor_id,
                        "mode": "dry_run",
                    },
                    "side_effects": "none",
                }
                warnings = ["tool_invoke_dry_run"]
            else:
                # Fail closed: live invocation requires exact version + hash pin.
                if not version or not tool_hash:
                    raise ServiceError(
                        "tool_hash_required",
                        "dry_run=false requires exact version and tool_hash/source_hash/bundle_hash",
                        http_status=400,
                    )
                if not actor.may_write():
                    raise ServiceError(
                        "auth_forbidden",
                        "live tool invocation requires write/execute permission",
                        http_status=403,
                    )
                # Prefer source_hash pin (always computed); accept bundle_hash alias.
                source_hash = params.get("source_hash")
                bundle_hash = params.get("bundle_hash")
                if source_hash is None and bundle_hash is None:
                    source_hash = tool_hash
                invocation = invoke_tool(
                    tool_dir,
                    tool_id=tool_id,
                    version=str(version),
                    bundle_hash=str(bundle_hash) if bundle_hash is not None else None,
                    source_hash=str(source_hash) if source_hash is not None else None,
                    argv=[str(a) for a in argv] or None,
                    cwd=tool_dir,
                    input_text=stdin,
                    adapter=str(params.get("adapter") or "local"),
                )
                if not invocation.ok:
                    raise ServiceError(
                        "tool_invoke_failed",
                        invocation.error or "packaged tool invocation failed",
                        http_status=502,
                    )
                result = {
                    "tool_id": invocation.tool_id,
                    "version": invocation.version,
                    "descriptor_hash": (
                        invocation.bundle_hash
                        or (
                            invocation.resolved.descriptor.source_hash
                            if invocation.resolved
                            else None
                        )
                    ),
                    "source_hash": (
                        invocation.resolved.descriptor.source_hash
                        if invocation.resolved
                        else None
                    ),
                    "bundle_hash": invocation.bundle_hash,
                    "dry_run": False,
                    "output": {
                        "exit_code": invocation.exit_code,
                        "stdout": invocation.stdout,
                        "stderr": invocation.stderr,
                        "adapter_kind": invocation.adapter_kind,
                        "invoked_by": actor.actor_id,
                        "mode": "live_adapter",
                    },
                    "side_effects": load_tool_descriptor(tool_dir).side_effect_class,
                }
                warnings = []
        except ResolutionError as exc:
            raise ServiceError("tool_resolve_failed", str(exc), http_status=409) from exc

        self._events.append(
            {
                "type": "tool_invocation",
                "tool_id": tool_id,
                "actor_id": actor.actor_id,
                "dry_run": dry_run,
                "at": _utc_now(),
            }
        )
        return {
            "data": result,
            "release_hash": skill.release_hash if skill else "",
            "profile_hash": skill.profile_hash if skill else "",
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
        clean = self._guard_params(prepare_feedback_params, params)
        run = self._get_run(str(clean["run_id"]), actor)
        if clean.get("skill_id") and str(clean["skill_id"]) != run.skill_id:
            raise ServiceError(
                "auth_forbidden",
                "feedback skill_id does not match accessible run",
                http_status=403,
            )
        record = {
            "feedback_id": str(uuid.uuid4()),
            "actor_id": actor.actor_id,
            "org_id": actor.org_id or "",
            "skill_id": clean.get("skill_id") or run.skill_id,
            "run_id": run.run_id,
            "kind": clean.get("kind") or "correction",
            "rating": clean.get("rating"),
            "friction": clean.get("friction"),
            "missing_step": clean.get("missing_step"),
            "outcome": clean.get("outcome"),
            "notes": clean.get("notes"),
            "at": _utc_now(),
        }
        self._feedback.append(record)
        self._store.append_feedback(record)
        run.feedback.append(record)
        self._persist_run(run)
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
        clean = self._guard_params(prepare_trace_params, params)
        run = self._get_run(str(clean["run_id"]), actor)
        if clean.get("skill_id") and str(clean["skill_id"]) != run.skill_id:
            raise ServiceError(
                "auth_forbidden",
                "trace skill_id does not match accessible run",
                http_status=403,
            )
        fingerprint = str(
            clean.get("fingerprint")
            or self._stable_hash(
                json.dumps(
                    {
                        "skill_id": clean.get("skill_id") or run.skill_id,
                        "run_id": run.run_id,
                        "summary": clean.get("summary"),
                        "actor_id": actor.actor_id,
                        "org_id": actor.org_id or "",
                    },
                    sort_keys=True,
                )
            )
        )
        existing = self._store.find_trace_by_fingerprint(fingerprint)
        if existing is not None:
            if existing.get("actor_id") != actor.actor_id or (existing.get("org_id") or "") != (
                actor.org_id or ""
            ):
                raise ServiceError(
                    "auth_forbidden",
                    "trace candidate belongs to another actor/org",
                    http_status=403,
                )
            return {
                "data": {**existing, "deduplicated": True},
                "warnings": ["duplicate_trace_candidate"],
            }
        record = {
            "candidate_id": str(uuid.uuid4()),
            "fingerprint": fingerprint,
            "actor_id": actor.actor_id,
            "org_id": actor.org_id or "",
            "skill_id": clean.get("skill_id") or run.skill_id,
            "run_id": run.run_id,
            "summary": clean.get("summary"),
            "observed": clean.get("observed") or {},
            "status": "queued",
            "at": _utc_now(),
            "deduplicated": False,
        }
        self._trace_candidates.append(record)
        self._store.append_trace(record)
        return {"data": record, "recommended_next": "enqueue_review"}
