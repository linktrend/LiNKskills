"""Postgres-backed GatewayStore adapter (psycopg v3).

Selected via ``LINKSKILLS_GATEWAY_STORE=postgres`` plus
``LINKSKILLS_DATABASE_URL`` or ``DATABASE_URL``. Implements the same
``GatewayStore`` Protocol surface as SQLite/in-memory stores.

RLS identity is applied per transaction with:
  SET LOCAL ROLE svc_lskills_runtime;
  SET LOCAL via set_config('app.current_actor_id', ..., true);
  SET LOCAL via set_config('app.current_org_id', ..., true);

Call ``bind_identity`` / ``identity(...)`` so reads/writes pass RLS.
Actor and org GUCs must be non-empty for tenant writes (fail closed);
null/empty PACI ``orgId`` is rejected before RLS-protected DML.
Nested writers inside ``run_atomic_idempotent`` defer commit so SET LOCAL
GUCs are not cleared mid-transaction (parity with SQLite ``_maybe_commit``).
When ``rls=False`` (superuser ephemeral proofs without role switch), GUCs
are still set but role is not switched.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterator, Mapping, Optional, Tuple

from .persistence import (
    IdempotencyReserveResult,
    _before_atomic_wait,
    _crash_after_mutation_requested,
    _lease_expired,
    _lease_expiry_iso,
    _new_fence_token,
    _run_to_dict,
    canonical_request_hash,
)

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]
    Jsonb = None  # type: ignore[assignment]


DEFAULT_RUNTIME_ROLE = "svc_lskills_runtime"


def resolve_database_url() -> Optional[str]:
    """Return Postgres DSN from LiNKskills or generic env vars."""
    for key in (
        "LINKSKILLS_DATABASE_URL",
        "DATABASE_URL",
        "LINKSKILLS_STORE_URL",
        "LINKSKILLS_POSTGRES_URL",
        "LINKSKILLS_EPHEMERAL_PG_URL",
    ):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return None


REQUIRED_GATEWAY_TABLES = (
    "idempotency",
    "side_effect_intents",
    "gateway_events",
    "skill_runs",
)


def _require_psycopg() -> Any:
    if psycopg is None:
        raise ImportError(
            "psycopg (v3) is required for PostgresGatewayStore. "
            "Install via: pip install 'linkskills-gateway[postgres]' "
            "or pip install 'psycopg[binary]>=3.1'."
        )
    return psycopg


def _as_jsonb(value: Any) -> Any:
    if Jsonb is None:
        return json.dumps(value)
    return Jsonb(value)


def _iso_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = str(value).strip()
    return text or None


def _parse_run_id(run_id: str) -> str:
    """Normalize run_id; Postgres skill_runs.run_id is uuid."""
    text = str(run_id).strip()
    try:
        return str(uuid.UUID(text))
    except ValueError as exc:
        raise ValueError(f"run_id must be a UUID for Postgres store: {run_id!r}") from exc


class PostgresGatewayStore:
    """Durable Postgres store matching GatewayStore Protocol semantics."""

    def __init__(
        self,
        dsn: str,
        *,
        role: str = DEFAULT_RUNTIME_ROLE,
        rls: bool = True,
    ) -> None:
        _require_psycopg()
        self.dsn = dsn
        self.role = role
        self.rls = rls
        self._lock = threading.RLock()
        self._conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=False)
        self._atomic_depth = 0
        self._crash_after_mutation = False
        self._identity = threading.local()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def probe_reachable(self) -> bool:
        """Cheap connectivity probe for /ready. Never returns secret material."""
        with self._lock:
            if not self._tx_idle():
                self._conn.rollback()
            with self._conn.cursor() as cur:
                cur.execute("select 1")
                cur.fetchone()
            self._conn.commit()
        return True

    def probe_schema_ready(self) -> bool:
        """True when gateway persistence migration tables exist (000007+)."""
        with self._lock:
            if not self._tx_idle():
                self._conn.rollback()
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    select table_name
                    from information_schema.tables
                    where table_schema = 'lskills'
                      and table_name = any(%s)
                    """,
                    (list(REQUIRED_GATEWAY_TABLES),),
                )
                found = {str(row["table_name"]) for row in cur.fetchall()}
            self._conn.commit()
        return set(REQUIRED_GATEWAY_TABLES).issubset(found)

    def bind_identity(self, actor_id: str, org_id: str) -> None:
        """Bind transaction-local RLS identity for subsequent operations.

        Empty org is stored as ``""`` so callers can detect missing tenant
        scope; write paths fail closed via ``_require_rls_identity``.
        """
        self._identity.actor_id = str(actor_id)
        self._identity.org_id = str(org_id or "")

    def clear_identity(self) -> None:
        self._identity.actor_id = None
        self._identity.org_id = None

    @contextmanager
    def identity(self, actor_id: str, org_id: str) -> Iterator["PostgresGatewayStore"]:
        previous = (
            getattr(self._identity, "actor_id", None),
            getattr(self._identity, "org_id", None),
        )
        self.bind_identity(actor_id, org_id)
        try:
            yield self
        finally:
            if previous[0] is None:
                self.clear_identity()
            else:
                self.bind_identity(str(previous[0]), str(previous[1] or ""))

    def _current_identity(
        self,
        *,
        actor_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        bound_actor = getattr(self._identity, "actor_id", None)
        bound_org = getattr(self._identity, "org_id", None)
        resolved_actor = str(actor_id if actor_id is not None else (bound_actor or ""))
        resolved_org = str(org_id if org_id is not None else (bound_org or ""))
        return resolved_actor, resolved_org

    @staticmethod
    def _require_rls_identity(actor_id: str, org_id: str) -> None:
        """Fail closed: RLS policies require non-empty actor + org GUCs.

        Matches ``lskills.actor_matches`` / ``lskills.org_matches`` (empty
        strings become NULL via ``nullif`` and deny all rows). Never invent
        a default org — PACI ``orgId`` null for service actors must be
        rejected before touching RLS-protected tables.
        """
        if not str(actor_id or "").strip():
            raise ValueError(
                "postgres RLS requires bound actor_id via bind_identity / "
                "identity() from verified PACI claims"
            )
        if not str(org_id or "").strip():
            raise ValueError(
                "postgres RLS requires bound org_id via bind_identity / "
                "identity() from verified PACI claims "
                "(null/empty orgId is fail-closed for write paths)"
            )

    def _apply_session_identity(
        self,
        cur: Any,
        *,
        actor_id: str,
        org_id: str,
    ) -> None:
        """SET LOCAL role + parameterized actor/org GUCs in the open transaction."""
        self._require_rls_identity(actor_id, org_id)
        if self.rls and self.role:
            # Role name is allowlisted (constructor default / explicit arg only).
            cur.execute(f"set local role {self.role}")
        # is_local=true ⇒ transaction-scoped; cleared on commit/rollback (no pool leak).
        cur.execute(
            "select set_config('app.current_actor_id', %s, true)",
            (actor_id,),
        )
        cur.execute(
            "select set_config('app.current_org_id', %s, true)",
            (org_id,),
        )

    def _tx_idle(self) -> bool:
        status = self._conn.info.transaction_status
        idle = getattr(psycopg.pq, "TransactionStatus", None)
        if idle is not None:
            return status == idle.IDLE
        return int(status) == 0

    def _begin(self, *, actor_id: str, org_id: str) -> Any:
        """Open or join a transaction and bind RLS identity via SET LOCAL.

        Nested writers inside ``run_atomic_idempotent`` (``_atomic_depth > 0``)
        must **not** rollback/commit the outer frame — that would clear SET LOCAL
        GUCs and break idempotency + skill_runs atomicity (SQLite uses the same
        deferred-commit pattern via ``_maybe_commit``).
        """
        self._require_rls_identity(actor_id, org_id)
        if self._atomic_depth > 0:
            # Join the outer atomic transaction; re-apply GUCs (still SET LOCAL).
            cur = self._conn.cursor()
            self._apply_session_identity(cur, actor_id=actor_id, org_id=org_id)
            return cur
        if not self._tx_idle():
            # Aborted or leftover transaction — reset before starting fresh.
            self._conn.rollback()
        cur = self._conn.cursor()
        self._apply_session_identity(cur, actor_id=actor_id, org_id=org_id)
        return cur

    def _maybe_commit(self) -> None:
        """Commit only when not nested inside an atomic idempotency transaction."""
        if self._atomic_depth == 0:
            self._conn.commit()

    def _commit(self) -> None:
        """Commit standalone / outer-frame work (not nested domain writers)."""
        self._maybe_commit()

    def _rollback(self) -> None:
        """Rollback only the outermost frame; nested failures defer to outer."""
        if self._atomic_depth == 0:
            try:
                self._conn.rollback()
            except Exception:  # pragma: no cover
                pass

    def reserve_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
    ) -> IdempotencyReserveResult:
        lease = _lease_expiry_iso()
        fence = _new_fence_token()
        _, org_id = self._current_identity(actor_id=actor_id)
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                try:
                    cur.execute(
                        """
                        insert into lskills.idempotency (
                          actor_id, org_id, operation, idempotency_key, request_hash,
                          status, envelope, lease_expires_at, fence_token, fence_generation
                        ) values (%s, %s, %s, %s, %s, 'reserved', null, %s::timestamptz, %s, 1)
                        """,
                        (actor_id, org_id, operation, key, request_hash, lease, fence),
                    )
                    self._commit()
                    return IdempotencyReserveResult("reserved", None, fence)
                except psycopg.IntegrityError:
                    self._conn.rollback()
                    cur = self._begin(actor_id=actor_id, org_id=org_id)
                    cur.execute(
                        """
                        select request_hash, status, envelope, lease_expires_at,
                               fence_token, fence_generation
                        from lskills.idempotency
                        where actor_id = %s and operation = %s and idempotency_key = %s
                        """,
                        (actor_id, operation, key),
                    )
                    row = cur.fetchone()
                    if row is None:
                        self._rollback()
                        raise
                    if str(row["request_hash"] or "") != request_hash:
                        self._commit()
                        return IdempotencyReserveResult("conflict")
                    if row["status"] == "completed" and row["envelope"] is not None:
                        envelope = row["envelope"]
                        if isinstance(envelope, str):
                            envelope = json.loads(envelope)
                        self._commit()
                        return IdempotencyReserveResult("replay", dict(envelope))
                    lease_iso = _iso_or_none(row["lease_expires_at"])
                    if row["status"] == "reserved" and not _lease_expired(lease_iso):
                        self._commit()
                        return IdempotencyReserveResult("in_progress")
                    generation = int(row["fence_generation"] or 0) + 1
                    cur.execute(
                        """
                        update lskills.idempotency
                        set status = 'reserved',
                            envelope = null,
                            lease_expires_at = %s::timestamptz,
                            request_hash = %s,
                            fence_token = %s,
                            fence_generation = %s,
                            org_id = %s,
                            updated_at = now()
                        where actor_id = %s and operation = %s and idempotency_key = %s
                        """,
                        (
                            lease,
                            request_hash,
                            fence,
                            generation,
                            org_id,
                            actor_id,
                            operation,
                            key,
                        ),
                    )
                    self._commit()
                    return IdempotencyReserveResult("reserved", None, fence)
            except Exception:
                self._rollback()
                raise

    def complete_idempotency(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        envelope: Mapping[str, Any],
        *,
        fence_token: str,
    ) -> None:
        _, org_id = self._current_identity(actor_id=actor_id)
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    update lskills.idempotency
                    set status = 'completed',
                        envelope = %s,
                        lease_expires_at = null,
                        updated_at = now()
                    where actor_id = %s and operation = %s and idempotency_key = %s
                      and request_hash = %s and fence_token = %s
                    """,
                    (
                        _as_jsonb(dict(envelope)),
                        actor_id,
                        operation,
                        key,
                        request_hash,
                        fence_token,
                    ),
                )
                if cur.rowcount == 0:
                    self._rollback()
                    raise ValueError("idempotency fence rejected: stale or displaced worker")
                self._commit()
            except Exception:
                self._rollback()
                raise

    def run_atomic_idempotent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        mutator: Callable[[], Mapping[str, Any]],
    ) -> IdempotencyReserveResult:
        _before_atomic_wait(self, key=key)
        lease = _lease_expiry_iso()
        fence = _new_fence_token()
        _, org_id = self._current_identity(actor_id=actor_id)
        with self._lock:
            self._atomic_depth += 1
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select request_hash, status, envelope, lease_expires_at, fence_generation
                    from lskills.idempotency
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        insert into lskills.idempotency (
                          actor_id, org_id, operation, idempotency_key, request_hash,
                          status, envelope, lease_expires_at, fence_token, fence_generation
                        ) values (%s, %s, %s, %s, %s, 'reserved', null, %s::timestamptz, %s, 1)
                        """,
                        (actor_id, org_id, operation, key, request_hash, lease, fence),
                    )
                else:
                    if str(row["request_hash"] or "") != request_hash:
                        # Early outcomes still need an outer commit (depth>0).
                        self._conn.commit()
                        return IdempotencyReserveResult("conflict")
                    if row["status"] == "completed" and row["envelope"] is not None:
                        envelope = row["envelope"]
                        if isinstance(envelope, str):
                            envelope = json.loads(envelope)
                        self._conn.commit()
                        return IdempotencyReserveResult("replay", dict(envelope))
                    lease_iso = _iso_or_none(row["lease_expires_at"])
                    if row["status"] == "reserved" and not _lease_expired(lease_iso):
                        self._conn.commit()
                        return IdempotencyReserveResult("in_progress")
                    generation = int(row["fence_generation"] or 0) + 1
                    cur.execute(
                        """
                        update lskills.idempotency
                        set status = 'reserved',
                            envelope = null,
                            lease_expires_at = %s::timestamptz,
                            request_hash = %s,
                            fence_token = %s,
                            fence_generation = %s,
                            org_id = %s,
                            updated_at = now()
                        where actor_id = %s and operation = %s and idempotency_key = %s
                        """,
                        (
                            lease,
                            request_hash,
                            fence,
                            generation,
                            org_id,
                            actor_id,
                            operation,
                            key,
                        ),
                    )
                # Nested domain writers (save_run etc.) defer commit while depth>0.
                envelope = dict(mutator())
                if _crash_after_mutation_requested(self, key=key):
                    raise RuntimeError(
                        "injected crash after mutation before idempotency complete"
                    )
                # Re-bind GUCs after nested writers; still same transaction.
                self._apply_session_identity(cur, actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    update lskills.idempotency
                    set status = 'completed',
                        envelope = %s,
                        lease_expires_at = null,
                        updated_at = now()
                    where actor_id = %s and operation = %s and idempotency_key = %s
                      and request_hash = %s and fence_token = %s
                    """,
                    (
                        _as_jsonb(envelope),
                        actor_id,
                        operation,
                        key,
                        request_hash,
                        fence,
                    ),
                )
                if cur.rowcount != 1:
                    self._conn.rollback()
                    raise ValueError("idempotency fence rejected during atomic complete")
                self._conn.commit()
                return IdempotencyReserveResult("replay", envelope, fence)
            except Exception:
                try:
                    self._conn.rollback()
                except Exception:  # pragma: no cover
                    pass
                raise
            finally:
                self._atomic_depth -= 1

    def record_side_effect_intent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        *,
        fence_token: str,
        downstream_key: str,
        request_hash: str,
    ) -> Dict[str, Any]:
        _, org_id = self._current_identity(actor_id=actor_id)
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select fence_token, status, request_hash from lskills.idempotency
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                row = cur.fetchone()
                if (
                    row is None
                    or str(row["fence_token"] or "") != fence_token
                    or str(row["status"] or "") != "reserved"
                ):
                    self._rollback()
                    raise ValueError("idempotency fence rejected for side-effect intent")
                cur.execute(
                    """
                    select status, fence_token, request_hash, downstream_key, result
                    from lskills.side_effect_intents
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                existing = cur.fetchone()
                if (
                    existing is not None
                    and str(existing["status"] or "") == "result"
                    and existing["result"] is not None
                ):
                    cur.execute(
                        """
                        update lskills.side_effect_intents
                        set fence_token = %s,
                            request_hash = %s,
                            downstream_key = %s,
                            org_id = %s,
                            updated_at = now()
                        where actor_id = %s and operation = %s and idempotency_key = %s
                        """,
                        (
                            fence_token,
                            request_hash,
                            downstream_key,
                            org_id,
                            actor_id,
                            operation,
                            key,
                        ),
                    )
                    result = existing["result"]
                    if isinstance(result, str):
                        result = json.loads(result)
                    self._commit()
                    return {
                        "status": "result",
                        "fence_token": fence_token,
                        "request_hash": request_hash,
                        "downstream_key": downstream_key,
                        "result": dict(result),
                    }
                cur.execute(
                    """
                    insert into lskills.side_effect_intents (
                      actor_id, org_id, operation, idempotency_key, fence_token,
                      request_hash, downstream_key, status, result
                    ) values (%s, %s, %s, %s, %s, %s, %s, 'intent', null)
                    on conflict (actor_id, operation, idempotency_key) do update set
                      fence_token = excluded.fence_token,
                      request_hash = excluded.request_hash,
                      downstream_key = excluded.downstream_key,
                      org_id = excluded.org_id,
                      status = 'intent',
                      result = null,
                      updated_at = now()
                    """,
                    (
                        actor_id,
                        org_id,
                        operation,
                        key,
                        fence_token,
                        request_hash,
                        downstream_key,
                    ),
                )
                self._commit()
                return {
                    "status": "intent",
                    "fence_token": fence_token,
                    "request_hash": request_hash,
                    "downstream_key": downstream_key,
                    "result": None,
                }
            except Exception:
                self._rollback()
                raise

    def complete_side_effect_intent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        *,
        fence_token: str,
        result: Mapping[str, Any],
    ) -> None:
        _, org_id = self._current_identity(actor_id=actor_id)
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select fence_token, status, request_hash from lskills.idempotency
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                reservation = cur.fetchone()
                if (
                    reservation is None
                    or str(reservation["status"] or "") != "reserved"
                    or str(reservation["fence_token"] or "") != fence_token
                ):
                    self._rollback()
                    raise ValueError(
                        "idempotency fence rejected: stale or displaced worker (reservation)"
                    )
                cur.execute(
                    """
                    select request_hash from lskills.side_effect_intents
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                intent = cur.fetchone()
                if intent is None:
                    self._rollback()
                    raise ValueError("idempotency fence rejected: missing side-effect intent")
                if str(intent["request_hash"] or "") != str(
                    reservation["request_hash"] or ""
                ):
                    self._rollback()
                    raise ValueError(
                        "idempotency fence rejected: intent request_hash mismatch"
                    )
                cur.execute(
                    """
                    update lskills.side_effect_intents
                    set status = 'result',
                        result = %s,
                        fence_token = %s,
                        updated_at = now()
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (
                        _as_jsonb(dict(result)),
                        fence_token,
                        actor_id,
                        operation,
                        key,
                    ),
                )
                if cur.rowcount != 1:
                    self._rollback()
                    raise ValueError("idempotency fence rejected for side-effect result")
                self._commit()
            except Exception:
                self._rollback()
                raise

    def get_side_effect_intent(
        self,
        actor_id: str,
        operation: str,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        # RLS GUCs from bind_identity only — lookup actor_id is a query key.
        guc_actor, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=guc_actor, org_id=org_id)
                cur.execute(
                    """
                    select status, fence_token, request_hash, downstream_key, result
                    from lskills.side_effect_intents
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                row = cur.fetchone()
                self._commit()
                if row is None:
                    return None
                result = row["result"]
                if isinstance(result, str):
                    result = json.loads(result)
                return {
                    "status": row["status"],
                    "fence_token": row["fence_token"],
                    "request_hash": row["request_hash"],
                    "downstream_key": row["downstream_key"],
                    "result": dict(result) if result is not None else None,
                }
            except Exception:
                self._rollback()
                raise

    def get_idempotent(
        self, actor_id: str, operation: str, key: str
    ) -> Optional[Dict[str, Any]]:
        # RLS GUCs come only from bind_identity / identity() — never from the
        # lookup actor_id argument (callers may probe foreign actor keys).
        guc_actor, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=guc_actor, org_id=org_id)
                cur.execute(
                    """
                    select envelope, status from lskills.idempotency
                    where actor_id = %s and operation = %s and idempotency_key = %s
                    """,
                    (actor_id, operation, key),
                )
                row = cur.fetchone()
                self._commit()
                if row is None or row["status"] != "completed" or row["envelope"] is None:
                    return None
                envelope = row["envelope"]
                if isinstance(envelope, str):
                    envelope = json.loads(envelope)
                return dict(envelope)
            except Exception:
                self._rollback()
                raise

    def put_idempotent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        envelope: Mapping[str, Any],
    ) -> Dict[str, Any]:
        request_hash = canonical_request_hash({"envelope": dict(envelope)})

        def mutator() -> Mapping[str, Any]:
            return dict(envelope)

        result = self.run_atomic_idempotent(actor_id, operation, key, request_hash, mutator)
        if result.outcome == "conflict":
            raise ValueError("idempotency conflict: same key, different request hash")
        if result.outcome == "in_progress":
            raise ValueError("idempotency in progress: retry later")
        if result.envelope is None:
            raise ValueError("idempotency envelope missing")
        return dict(result.envelope)

    def save_run(self, run: Any) -> None:
        payload = _run_to_dict(run)
        payload_actor = str(payload["actor_id"])
        payload_org = str(payload.get("org_id") or "")
        bound_actor, bound_org = self._current_identity()
        if bound_actor:
            # Prefer PACI-bound identity; reject payload disagreement (no spoof).
            if payload_actor and payload_actor != bound_actor:
                raise ValueError(
                    f"skill_runs actor_id {payload_actor!r} disagrees with "
                    f"bound identity actor_id {bound_actor!r}"
                )
            if payload_org and payload_org != bound_org:
                raise ValueError(
                    f"skill_runs org_id {payload_org!r} disagrees with "
                    f"bound identity org_id {bound_org!r}"
                )
            actor_id, org_id = bound_actor, bound_org
        else:
            actor_id, org_id = payload_actor, payload_org
            self.bind_identity(actor_id, org_id)
        run_id = _parse_run_id(str(payload["run_id"]))
        status = str(payload["status"])
        outcome = payload.get("outcome")
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    insert into lskills.skill_runs (
                      run_id, skill_id, version, release_hash, profile_hash,
                      actor_id, org_id, status, outcome, events_json, feedback_json,
                      idempotency_key, created_at, updated_at
                    ) values (
                      %s::uuid, %s, %s, %s, %s, %s, %s, %s::lskills.run_status,
                      %s, %s, %s, %s,
                      coalesce(%s::timestamptz, now()),
                      coalesce(%s::timestamptz, now())
                    )
                    on conflict (run_id) do update set
                      status = excluded.status,
                      outcome = excluded.outcome,
                      events_json = excluded.events_json,
                      feedback_json = excluded.feedback_json,
                      updated_at = excluded.updated_at
                    """,
                    (
                        run_id,
                        payload["skill_id"],
                        payload["version"],
                        payload.get("release_hash") or None,
                        payload.get("profile_hash") or None,
                        actor_id,
                        org_id,
                        status,
                        _as_jsonb(outcome if outcome is not None else {}),
                        _as_jsonb(payload.get("events") or []),
                        _as_jsonb(payload.get("feedback") or []),
                        payload.get("idempotency_key"),
                        payload.get("created_at"),
                        payload.get("updated_at"),
                    ),
                )
                self._maybe_commit()
            except Exception:
                self._rollback()
                raise

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        actor_id, org_id = self._current_identity()
        normalized = _parse_run_id(run_id)
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select run_id, skill_id, version, release_hash, profile_hash,
                           actor_id, org_id, status, outcome, events_json, feedback_json,
                           idempotency_key, created_at, updated_at
                    from lskills.skill_runs
                    where run_id = %s::uuid
                    """,
                    (normalized,),
                )
                row = cur.fetchone()
                self._commit()
                if row is None:
                    return None
                events = row.get("events_json") or []
                feedback = row.get("feedback_json") or []
                if isinstance(events, str):
                    events = json.loads(events)
                if isinstance(feedback, str):
                    feedback = json.loads(feedback)
                outcome = row.get("outcome")
                if isinstance(outcome, str):
                    outcome = json.loads(outcome)
                if outcome == {}:
                    outcome = None
                return {
                    "run_id": str(row["run_id"]),
                    "skill_id": row["skill_id"],
                    "version": row["version"],
                    "release_hash": row["release_hash"] or "",
                    "profile_hash": row["profile_hash"] or "",
                    "actor_id": row["actor_id"],
                    "org_id": row["org_id"],
                    "status": str(row["status"]),
                    "created_at": _iso_or_none(row["created_at"]) or "",
                    "updated_at": _iso_or_none(row["updated_at"]) or "",
                    "events": list(events),
                    "feedback": list(feedback),
                    "outcome": outcome,
                    "idempotency_key": row["idempotency_key"],
                }
            except Exception:
                self._rollback()
                raise

    def append_feedback(self, record: Mapping[str, Any]) -> None:
        payload = dict(record)
        actor_id = str(payload.get("actor_id") or "")
        org_id = str(payload.get("org_id") or "")
        self.bind_identity(actor_id, org_id)
        feedback_id = str(payload.get("feedback_id") or uuid.uuid4())
        run_id_raw = payload.get("run_id")
        run_id = _parse_run_id(str(run_id_raw)) if run_id_raw else None
        kind = str(payload.get("kind") or "other")
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    insert into lskills.feedback (
                      feedback_id, run_id, skill_id, actor_id, org_id, kind, payload, created_at
                    ) values (
                      %s::uuid, %s::uuid, %s, %s, %s, %s::lskills.feedback_kind, %s,
                      coalesce(%s::timestamptz, now())
                    )
                    on conflict (feedback_id) do nothing
                    """,
                    (
                        feedback_id,
                        run_id,
                        payload.get("skill_id"),
                        actor_id,
                        org_id,
                        kind,
                        _as_jsonb(payload),
                        payload.get("at") or payload.get("created_at"),
                    ),
                )
                self._commit()
            except Exception:
                self._rollback()
                raise

    def find_trace_by_fingerprint(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        actor_id, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select observed, candidate_id, fingerprint, actor_id, org_id,
                           skill_id, run_id, summary, status, created_at
                    from lskills.trace_to_eval_candidates
                    where fingerprint = %s
                    """,
                    (fingerprint,),
                )
                row = cur.fetchone()
                self._commit()
                if row is None:
                    return None
                observed = row.get("observed") or {}
                if isinstance(observed, str):
                    observed = json.loads(observed)
                if isinstance(observed, dict) and observed.get("fingerprint"):
                    return dict(observed)
                return {
                    "candidate_id": str(row["candidate_id"]),
                    "fingerprint": row["fingerprint"],
                    "actor_id": row["actor_id"],
                    "org_id": row["org_id"],
                    "skill_id": row.get("skill_id"),
                    "run_id": str(row["run_id"]) if row.get("run_id") else None,
                    "summary": row.get("summary"),
                    "status": str(row.get("status") or ""),
                    "at": _iso_or_none(row.get("created_at")),
                    **dict(observed),
                }
            except Exception:
                self._rollback()
                raise

    def append_trace(self, record: Mapping[str, Any]) -> None:
        payload = dict(record)
        actor_id = str(payload.get("actor_id") or "")
        org_id = str(payload.get("org_id") or "")
        self.bind_identity(actor_id, org_id)
        candidate_id = str(payload.get("candidate_id") or uuid.uuid4())
        fingerprint = str(payload.get("fingerprint") or "")
        run_id_raw = payload.get("run_id")
        run_id = _parse_run_id(str(run_id_raw)) if run_id_raw else None
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    insert into lskills.trace_to_eval_candidates (
                      candidate_id, fingerprint, run_id, skill_id, actor_id, org_id,
                      summary, observed, status, created_at
                    ) values (
                      %s::uuid, %s, %s::uuid, %s, %s, %s, %s, %s,
                      'queued'::lskills.trace_candidate_status,
                      coalesce(%s::timestamptz, now())
                    )
                    on conflict (fingerprint) do nothing
                    """,
                    (
                        candidate_id,
                        fingerprint,
                        run_id,
                        payload.get("skill_id"),
                        actor_id,
                        org_id,
                        payload.get("summary"),
                        _as_jsonb(payload),
                        payload.get("at") or payload.get("created_at"),
                    ),
                )
                self._commit()
            except Exception:
                self._rollback()
                raise

    def append_event(self, record: Mapping[str, Any]) -> None:
        payload = dict(record)
        actor_id = str(payload.get("actor_id") or getattr(self._identity, "actor_id", None) or "")
        org_id = str(payload.get("org_id") or getattr(self._identity, "org_id", None) or "")
        run_id_raw = payload.get("run_id")
        run_id = None
        if run_id_raw:
            try:
                run_id = _parse_run_id(str(run_id_raw))
            except ValueError:
                run_id = None
        with self._lock:
            try:
                if actor_id or org_id:
                    # Tenant-scoped event — fail closed without both actor and org.
                    if actor_id:
                        self.bind_identity(actor_id, org_id)
                    cur = self._begin(actor_id=actor_id, org_id=org_id)
                else:
                    # Anonymous spine row (null actor/org) allowed by 000007 policy.
                    if self._atomic_depth == 0 and not self._tx_idle():
                        self._conn.rollback()
                    cur = self._conn.cursor()
                    if self.rls and self.role:
                        cur.execute(f"set local role {self.role}")
                    cur.execute(
                        "select set_config('app.current_actor_id', '', true)"
                    )
                    cur.execute(
                        "select set_config('app.current_org_id', '', true)"
                    )
                if run_id is not None:
                    cur.execute(
                        """
                        insert into lskills.run_events (run_id, event_type, payload)
                        values (%s::uuid, %s, %s)
                        """,
                        (
                            run_id,
                            str(payload.get("type") or payload.get("event_type") or "event"),
                            _as_jsonb(payload),
                        ),
                    )
                cur.execute(
                    """
                    insert into lskills.gateway_events (actor_id, org_id, run_id, payload)
                    values (%s, %s, %s, %s)
                    """,
                    (
                        actor_id or None,
                        org_id or None,
                        run_id,
                        _as_jsonb(payload),
                    ),
                )
                self._maybe_commit()
            except Exception:
                self._rollback()
                raise
