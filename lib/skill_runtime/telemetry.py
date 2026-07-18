"""Skill invocation telemetry: local ledger buffer + optional Supabase flush.

Local ``execution_ledger.jsonl`` remains the durable on-disk buffer. When
Supabase credentials are present, events are also inserted into
``lskills.telemetry``. A separate flush path re-plays unsent buffer lines.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TELEMETRY_STATUSES = (
    "initialized",
    "in_progress",
    "pending_approval",
    "completed",
    "failed",
)


@dataclass
class InvocationEvent:
    """One skill invocation observation (never an authorization decision)."""

    skill: str
    status: str
    summary: str
    task_id: Optional[str] = None
    skill_version: Optional[str] = None
    agent_id: Optional[str] = None
    program_ref: Optional[str] = None
    issue_ref: Optional[str] = None
    run_ref: Optional[str] = None
    duration_ms: Optional[int] = None
    cost: Optional[Dict[str, Any]] = None
    outcome_detail: Optional[Dict[str, Any]] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    def __post_init__(self) -> None:
        status = self.status.lower()
        if status not in TELEMETRY_STATUSES:
            raise ValueError(
                f"status '{self.status}' must be one of {TELEMETRY_STATUSES}"
            )
        self.status = status

    def to_ledger_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        # Keep legacy key name `skill` for execution_ledger.jsonl compatibility.
        return {key: value for key, value in payload.items() if value is not None}

    def to_supabase_row(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "skill_id": self.skill,
            "skill_version": self.skill_version,
            "agent_id": self.agent_id,
            "program_ref": self.program_ref,
            "issue_ref": self.issue_ref,
            "run_ref": self.run_ref,
            "task_id": self.task_id,
            "status": self.status,
            "outcome_detail": self.outcome_detail if self.outcome_detail is not None else {},
            "duration_ms": self.duration_ms,
            "cost": self.cost,
            "summary": self.summary,
            "created_at": self.timestamp,
        }


def default_ledger_path(repo_root: Path) -> Path:
    return repo_root / "execution_ledger.jsonl"


def append_local_ledger(event: InvocationEvent, ledger_path: Path) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.to_ledger_dict(), ensure_ascii=True) + "\n")


def _supabase_config() -> Optional[Dict[str, str]]:
    """Resolve stage/prod URL + key from environment (GSM-rendered or local .env)."""
    target = os.environ.get("LIBRARIAN_TARGET_ENV", "stage").strip().lower()
    if target == "prod":
        url = os.environ.get("LINKTREND_PLATFORM_PROD_SUPABASE_URL") or os.environ.get(
            "SUPABASE_URL"
        )
        key = os.environ.get(
            "LINKTREND_PLATFORM_PROD_SUPABASE_SECRET_KEY"
        ) or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    else:
        url = os.environ.get("LINKTREND_PLATFORM_STAGE_SUPABASE_URL") or os.environ.get(
            "SUPABASE_URL"
        )
        key = os.environ.get(
            "LINKTREND_PLATFORM_STAGE_SUPABASE_SECRET_KEY"
        ) or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return {"url": url.rstrip("/"), "key": key}


def insert_telemetry_rows(rows: Sequence[Dict[str, Any]]) -> None:
    """Insert rows into lskills.telemetry via PostgREST. Raises on HTTP failure."""
    cfg = _supabase_config()
    if cfg is None:
        raise RuntimeError(
            "Supabase credentials not configured "
            "(LINKTREND_PLATFORM_*_SUPABASE_URL + SECRET_KEY or SUPABASE_*)"
        )
    endpoint = f"{cfg['url']}/rest/v1/telemetry"
    body = json.dumps(list(rows)).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "apikey": cfg["key"],
            "Authorization": f"Bearer {cfg['key']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
            "Accept-Profile": "lskills",
            "Content-Profile": "lskills",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(f"telemetry insert HTTP {response.status}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"telemetry insert failed: {exc.code} {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"telemetry insert network error: {exc}") from exc


def record_invocation(
    event: InvocationEvent,
    *,
    repo_root: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    write_supabase: bool = True,
) -> Dict[str, Any]:
    """Append to local ledger; optionally mirror to ``lskills.telemetry``.

    Returns a result dict: ``{local: bool, supabase: 'written'|'skipped'|'failed', error?}``.
    Local write always happens; Supabase failure does not undo the local buffer.
    """
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    path = ledger_path or default_ledger_path(root)
    append_local_ledger(event, path)
    result: Dict[str, Any] = {"local": True, "supabase": "skipped", "event_id": event.event_id}

    if not write_supabase:
        return result
    if _supabase_config() is None:
        return result

    try:
        insert_telemetry_rows([event.to_supabase_row()])
        result["supabase"] = "written"
    except Exception as exc:  # noqa: BLE001 — callers need a soft failure path
        result["supabase"] = "failed"
        result["error"] = str(exc)
    return result


def flush_telemetry_buffer(
    *,
    repo_root: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    limit: int = 500,
) -> Dict[str, Any]:
    """Flush recent ledger lines that look like extended events into Supabase.

    Lines without ``event_id`` (legacy) are skipped. Already-flushed event_ids are
    not tracked in a side store; PostgREST insert uses event_id PK — duplicates
    fail closed and are counted as ``duplicate_or_error``.
    """
    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    path = ledger_path or default_ledger_path(root)
    if not path.is_file():
        return {"attempted": 0, "written": 0, "skipped": 0, "failed": 0}

    lines = path.read_text(encoding="utf-8").splitlines()
    candidates: List[Dict[str, Any]] = []
    skipped = 0
    for raw in reversed(lines):
        if len(candidates) >= limit:
            break
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if "event_id" not in payload or "skill" not in payload:
            skipped += 1
            continue
        event = InvocationEvent(
            skill=payload["skill"],
            status=str(payload.get("status", "completed")),
            summary=str(payload.get("summary", "")),
            task_id=payload.get("task_id"),
            skill_version=payload.get("skill_version"),
            agent_id=payload.get("agent_id"),
            program_ref=payload.get("program_ref"),
            issue_ref=payload.get("issue_ref"),
            run_ref=payload.get("run_ref"),
            duration_ms=payload.get("duration_ms"),
            cost=payload.get("cost"),
            outcome_detail=payload.get("outcome_detail"),
            event_id=payload["event_id"],
            timestamp=payload.get("timestamp")
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        candidates.append(event.to_supabase_row())

    if not candidates:
        return {"attempted": 0, "written": 0, "skipped": skipped, "failed": 0}

    written = 0
    failed = 0
    for row in candidates:
        try:
            insert_telemetry_rows([row])
            written += 1
        except Exception:  # noqa: BLE001
            failed += 1
    return {
        "attempted": len(candidates),
        "written": written,
        "skipped": skipped,
        "failed": failed,
    }
