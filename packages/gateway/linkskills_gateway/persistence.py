"""SQLite-backed durable store for Gateway runs, telemetry, and idempotency."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional, Protocol, Tuple, runtime_checkable


DEFAULT_STATE_DIRNAME = ".linkskills-state"
GATEWAY_DB_NAME = "gateway.sqlite"

IdempotencyOutcome = Literal["reserved", "replay", "conflict"]


def resolve_state_dir(
    *,
    repo_root: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    """Resolve durable state directory from explicit path or environment."""
    if state_dir is not None:
        return Path(state_dir).expanduser().resolve()
    env = os.environ.get("LINKSKILLS_STATE_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    root = Path(repo_root) if repo_root else Path.cwd()
    return (root / DEFAULT_STATE_DIRNAME).resolve()


def gateway_db_path(state_dir: Path) -> Path:
    return Path(state_dir) / GATEWAY_DB_NAME


def durable_enabled(
    *,
    state_dir: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> bool:
    if state_dir is not None:
        return True
    if os.environ.get("LINKSKILLS_GATEWAY_DURABLE", "").strip() in {"1", "true", "yes"}:
        return True
    resolved = resolve_state_dir(repo_root=repo_root)
    return resolved.exists() and (resolved / GATEWAY_DB_NAME).is_file()


def canonical_request_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA-256 of a canonical JSON request binding."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@runtime_checkable
class GatewayStore(Protocol):
    """Durable or in-memory persistence contract for SkillsGatewayService."""

    def reserve_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
    ) -> Tuple[IdempotencyOutcome, Optional[Dict[str, Any]]]:
        ...

    def complete_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        envelope: Mapping[str, Any],
    ) -> None:
        ...

    def get_idempotent(self, actor_id: str, operation: str, key: str) -> Optional[Dict[str, Any]]:
        ...

    def put_idempotent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        ...

    def save_run(self, run: Any) -> None:
        ...

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        ...

    def append_feedback(self, record: Mapping[str, Any]) -> None:
        ...

    def find_trace_by_fingerprint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        ...

    def append_trace(self, record: Mapping[str, Any]) -> None:
        ...

    def append_event(self, record: Mapping[str, Any]) -> None:
        ...


class InMemoryGatewayStore:
    """Process-local store used when durable SQLite is not configured."""

    def __init__(self) -> None:
        self._idempotency: Dict[str, Dict[str, Any]] = {}
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._feedback: List[Dict[str, Any]] = []
        self._traces: List[Dict[str, Any]] = []
        self._events: List[Dict[str, Any]] = []

    @staticmethod
    def _idempotency_key(actor_id: str, operation: str, key: str) -> str:
        return f"{actor_id}:{operation}:{key}"

    def reserve_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
    ) -> Tuple[IdempotencyOutcome, Optional[Dict[str, Any]]]:
        cache_key = self._idempotency_key(actor_id, operation, key)
        existing = self._idempotency.get(cache_key)
        if existing is None:
            self._idempotency[cache_key] = {
                "request_hash": request_hash,
                "status": "reserved",
                "envelope": None,
            }
            return "reserved", None
        if str(existing.get("request_hash") or "") != request_hash:
            return "conflict", None
        if existing.get("status") == "completed" and existing.get("envelope") is not None:
            return "replay", dict(existing["envelope"])
        # Same hash, still reserved (or incomplete) — allow caller to proceed/retry.
        return "reserved", None

    def complete_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        envelope: Mapping[str, Any],
    ) -> None:
        cache_key = self._idempotency_key(actor_id, operation, key)
        existing = self._idempotency.get(cache_key)
        if existing is None:
            self._idempotency[cache_key] = {
                "request_hash": request_hash,
                "status": "completed",
                "envelope": dict(envelope),
            }
            return
        if str(existing.get("request_hash") or "") != request_hash:
            raise ValueError("idempotency request_hash mismatch on complete")
        existing["status"] = "completed"
        existing["envelope"] = dict(envelope)

    def get_idempotent(self, actor_id: str, operation: str, key: str) -> Optional[Dict[str, Any]]:
        row = self._idempotency.get(self._idempotency_key(actor_id, operation, key))
        if row is None or row.get("status") != "completed" or row.get("envelope") is None:
            return None
        return dict(row["envelope"])

    def put_idempotent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        # Legacy helper — binds hash to envelope body for callers that skip reserve.
        request_hash = canonical_request_hash({"envelope": dict(envelope)})
        outcome, cached = self.reserve_idempotency(actor_id, operation, key, request_hash)
        if outcome == "conflict":
            raise ValueError("idempotency conflict: same key, different request hash")
        if outcome == "replay" and cached is not None:
            return cached
        self.complete_idempotency(actor_id, operation, key, request_hash, envelope)
        return dict(envelope)

    def save_run(self, run: Any) -> None:
        payload = _run_to_dict(run)
        self._runs[str(payload["run_id"])] = payload

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._runs.get(run_id)
        return dict(row) if row is not None else None

    def append_feedback(self, record: Mapping[str, Any]) -> None:
        self._feedback.append(dict(record))

    def find_trace_by_fingerprint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        for item in self._traces:
            if item.get("fingerprint") == fingerprint:
                return dict(item)
        return None

    def append_trace(self, record: Mapping[str, Any]) -> None:
        self._traces.append(dict(record))

    def append_event(self, record: Mapping[str, Any]) -> None:
        self._events.append(dict(record))


class SqliteGatewayStore:
    """Durable SQLite store under LINKSKILLS_STATE_DIR or repo/.linkskills-state/."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            pragma journal_mode = wal;
            create table if not exists idempotency (
              actor_id text not null,
              operation text not null,
              idempotency_key text not null,
              request_hash text not null default '',
              status text not null default 'completed',
              envelope_json text,
              created_at text not null default (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
              primary key (actor_id, operation, idempotency_key)
            );
            create table if not exists skill_runs (
              run_id text primary key,
              skill_id text not null,
              version text not null,
              release_hash text,
              profile_hash text,
              actor_id text not null,
              org_id text not null,
              status text not null,
              outcome_json text,
              events_json text not null default '[]',
              feedback_json text not null default '[]',
              idempotency_key text,
              created_at text not null,
              updated_at text not null
            );
            create index if not exists skill_runs_actor_org_idx
              on skill_runs (actor_id, org_id);
            create table if not exists feedback (
              feedback_id text primary key,
              actor_id text not null,
              org_id text not null,
              run_id text,
              skill_id text,
              payload_json text not null,
              created_at text not null
            );
            create table if not exists trace_candidates (
              candidate_id text primary key,
              fingerprint text not null unique,
              actor_id text not null,
              org_id text not null,
              skill_id text,
              run_id text,
              payload_json text not null,
              created_at text not null
            );
            create table if not exists gateway_events (
              event_id integer primary key autoincrement,
              payload_json text not null,
              created_at text not null default (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            );
            """
        )
        cols = {
            row["name"]
            for row in self._conn.execute("pragma table_info(idempotency)").fetchall()
        }
        if "request_hash" not in cols:
            self._conn.execute(
                "alter table idempotency add column request_hash text not null default ''"
            )
        if "status" not in cols:
            self._conn.execute(
                "alter table idempotency add column status text not null default 'completed'"
            )
        # Older rows stored envelope_json NOT NULL; allow null for reservations.
        self._conn.commit()

    def reserve_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
    ) -> Tuple[IdempotencyOutcome, Optional[Dict[str, Any]]]:
        try:
            self._conn.execute(
                """
                insert into idempotency (
                  actor_id, operation, idempotency_key, request_hash, status, envelope_json
                ) values (?, ?, ?, ?, 'reserved', null)
                """,
                (actor_id, operation, key, request_hash),
            )
            self._conn.commit()
            return "reserved", None
        except sqlite3.IntegrityError:
            row = self._conn.execute(
                """
                select request_hash, status, envelope_json from idempotency
                where actor_id = ? and operation = ? and idempotency_key = ?
                """,
                (actor_id, operation, key),
            ).fetchone()
            if row is None:
                raise
            if str(row["request_hash"] or "") != request_hash:
                return "conflict", None
            if row["status"] == "completed" and row["envelope_json"]:
                return "replay", json.loads(row["envelope_json"])
            return "reserved", None

    def complete_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        envelope: Mapping[str, Any],
    ) -> None:
        payload = json.dumps(dict(envelope), sort_keys=True)
        cur = self._conn.execute(
            """
            update idempotency
            set status = 'completed', envelope_json = ?
            where actor_id = ? and operation = ? and idempotency_key = ?
              and request_hash = ?
            """,
            (payload, actor_id, operation, key, request_hash),
        )
        if cur.rowcount == 0:
            # Insert completed row if reserve was skipped.
            try:
                self._conn.execute(
                    """
                    insert into idempotency (
                      actor_id, operation, idempotency_key, request_hash, status, envelope_json
                    ) values (?, ?, ?, ?, 'completed', ?)
                    """,
                    (actor_id, operation, key, request_hash, payload),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("idempotency request_hash mismatch on complete") from exc
        self._conn.commit()

    def get_idempotent(self, actor_id: str, operation: str, key: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            """
            select envelope_json, status from idempotency
            where actor_id = ? and operation = ? and idempotency_key = ?
            """,
            (actor_id, operation, key),
        ).fetchone()
        if row is None or row["status"] != "completed" or not row["envelope_json"]:
            return None
        return json.loads(row["envelope_json"])

    def put_idempotent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        request_hash = canonical_request_hash({"envelope": dict(envelope)})
        outcome, cached = self.reserve_idempotency(actor_id, operation, key, request_hash)
        if outcome == "conflict":
            raise ValueError("idempotency conflict: same key, different request hash")
        if outcome == "replay" and cached is not None:
            return cached
        self.complete_idempotency(actor_id, operation, key, request_hash, envelope)
        return dict(envelope)

    def save_run(self, run: Any) -> None:
        payload = _run_to_dict(run)
        self._conn.execute(
            """
            insert into skill_runs (
              run_id, skill_id, version, release_hash, profile_hash,
              actor_id, org_id, status, outcome_json, events_json, feedback_json,
              idempotency_key, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(run_id) do update set
              status = excluded.status,
              outcome_json = excluded.outcome_json,
              events_json = excluded.events_json,
              feedback_json = excluded.feedback_json,
              updated_at = excluded.updated_at
            """,
            (
                payload["run_id"],
                payload["skill_id"],
                payload["version"],
                payload.get("release_hash"),
                payload.get("profile_hash"),
                payload["actor_id"],
                payload["org_id"],
                payload["status"],
                json.dumps(payload.get("outcome")),
                json.dumps(payload.get("events") or []),
                json.dumps(payload.get("feedback") or []),
                payload.get("idempotency_key"),
                payload["created_at"],
                payload["updated_at"],
            ),
        )
        self._conn.commit()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "select * from skill_runs where run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "run_id": row["run_id"],
            "skill_id": row["skill_id"],
            "version": row["version"],
            "release_hash": row["release_hash"] or "",
            "profile_hash": row["profile_hash"] or "",
            "actor_id": row["actor_id"],
            "org_id": row["org_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "events": json.loads(row["events_json"]),
            "feedback": json.loads(row["feedback_json"]),
            "outcome": json.loads(row["outcome_json"]) if row["outcome_json"] else None,
            "idempotency_key": row["idempotency_key"],
        }

    def append_feedback(self, record: Mapping[str, Any]) -> None:
        payload = dict(record)
        self._conn.execute(
            """
            insert into feedback (
              feedback_id, actor_id, org_id, run_id, skill_id, payload_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(payload.get("feedback_id")),
                str(payload.get("actor_id")),
                str(payload.get("org_id")),
                payload.get("run_id"),
                payload.get("skill_id"),
                json.dumps(payload, sort_keys=True),
                str(payload.get("at") or payload.get("created_at") or ""),
            ),
        )
        self._conn.commit()

    def find_trace_by_fingerprint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "select payload_json from trace_candidates where fingerprint = ?",
            (fingerprint,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload_json"])

    def append_trace(self, record: Mapping[str, Any]) -> None:
        payload = dict(record)
        self._conn.execute(
            """
            insert into trace_candidates (
              candidate_id, fingerprint, actor_id, org_id, skill_id, run_id,
              payload_json, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(payload.get("candidate_id")),
                str(payload.get("fingerprint")),
                str(payload.get("actor_id")),
                str(payload.get("org_id")),
                payload.get("skill_id"),
                payload.get("run_id"),
                json.dumps(payload, sort_keys=True),
                str(payload.get("at") or payload.get("created_at") or ""),
            ),
        )
        self._conn.commit()

    def append_event(self, record: Mapping[str, Any]) -> None:
        self._conn.execute(
            "insert into gateway_events (payload_json) values (?)",
            (json.dumps(dict(record), sort_keys=True),),
        )
        self._conn.commit()


def open_gateway_store(
    *,
    repo_root: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    store: Optional[GatewayStore] = None,
) -> GatewayStore:
    """Open durable SQLite when state_dir is provided or durable env is set."""
    if store is not None:
        return store
    use_durable = state_dir is not None or os.environ.get(
        "LINKSKILLS_GATEWAY_DURABLE", ""
    ).strip() in {"1", "true", "yes"}
    if not use_durable:
        return InMemoryGatewayStore()
    resolved = resolve_state_dir(repo_root=repo_root, state_dir=state_dir)
    return SqliteGatewayStore(gateway_db_path(resolved))


def _run_to_dict(run: Any) -> Dict[str, Any]:
    if is_dataclass(run):
        return asdict(run)
    if isinstance(run, Mapping):
        return dict(run)
    raise TypeError(f"unsupported run type: {type(run)!r}")
