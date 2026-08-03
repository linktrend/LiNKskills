#!/usr/bin/env python3
"""Ephemeral Postgres proofs for GatewayStore + review_queue RLS.

Enabled when:
- ``LINKSKILLS_EPHEMERAL_PG_URL`` or ``LINKSKILLS_TEST_PG_DSN`` is set, or
- Docker is available and ``LINKSKILLS_TEST_PG_DOCKER`` is not ``0``/``skip``.

Never applies to production datasets. Uses an ephemeral container or DSN only.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "librarian_domain"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))

MIGRATIONS = REPO_ROOT / "supabase" / "migrations"
FOUNDATION_SQL = MIGRATIONS / "20260727_000005_lskills_registry_foundation.sql"
UPGRADE_SQL = MIGRATIONS / "20260728_000006_lskills_rls_actor_org_scope.sql"
GATEWAY_SQL = MIGRATIONS / "20260730_000007_lskills_gateway_persistence.sql"
REVIEW_QUEUE_SQL = MIGRATIONS / "20260730_000008_lskills_review_queue.sql"
REVIEW_QUEUE_ACTOR_SQL = (
    MIGRATIONS / "20260730_000009_lskills_review_queue_actor_isolation.sql"
)
BOOTSTRAP_SQL = """
create extension if not exists "pgcrypto";
create schema if not exists platform;
create schema if not exists lskills;
create table if not exists platform.organizations (
  id uuid primary key default gen_random_uuid()
);
do $$
begin
  if not exists (
    select 1 from pg_type
    where typname = 'member_role' and typnamespace = 'platform'::regnamespace
  ) then
    create type platform.member_role as enum ('viewer', 'member', 'admin');
  end if;
end $$;
do $$
begin
  if not exists (
    select 1 from pg_type
    where typname = 'certification_state' and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.certification_state as enum ('draft', 'eval_pending', 'usable', 'deprecated');
  end if;
end $$;
create or replace function platform.has_org_access(org uuid, min_role platform.member_role)
returns boolean language sql stable as $$ select true $$;
"""


def _import_psycopg():
    try:
        import psycopg  # type: ignore

        return psycopg
    except ImportError:
        return None


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _resolve_dsn() -> str | None:
    for key in ("LINKSKILLS_EPHEMERAL_PG_URL", "LINKSKILLS_TEST_PG_DSN"):
        env = os.environ.get(key, "").strip()
        if env:
            return env
    return None


def _explicitly_enabled() -> bool:
    if _resolve_dsn():
        return True
    flag = os.environ.get("LINKSKILLS_TEST_PG_DOCKER", "").strip().lower()
    if flag in {"0", "false", "no", "skip", "off"}:
        return False
    if flag in {"1", "true", "yes"}:
        return _docker_available()
    return _docker_available()


def _should_use_docker() -> bool:
    return _resolve_dsn() is None and _explicitly_enabled() and _docker_available()


def _free_host_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_docker_postgres() -> tuple[str, str]:
    container_id = f"linkskills-gw-{uuid.uuid4().hex[:8]}"
    host_port = _free_host_port()
    dsn = f"postgresql://postgres:postgres@127.0.0.1:{host_port}/linkskills_gw_test"
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            container_id,
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-e",
            "POSTGRES_DB=linkskills_gw_test",
            "-p",
            f"{host_port}:5432",
            "postgres:16-alpine",
        ],
        capture_output=True,
        text=True,
    )
    if started.returncode != 0:
        raise unittest.SkipTest(
            "docker postgres failed to start: "
            + (started.stderr or started.stdout or "unknown error")
        )
    psycopg = _import_psycopg()
    if psycopg is None:
        subprocess.run(["docker", "rm", "-f", container_id], check=False)
        raise unittest.SkipTest("psycopg required for ephemeral gateway postgres tests")
    last_err: Exception | None = None
    for _ in range(60):
        probe = subprocess.run(
            ["docker", "exec", container_id, "pg_isready", "-U", "postgres"],
            capture_output=True,
        )
        if probe.returncode == 0:
            try:
                with psycopg.connect(dsn, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute("select 1")
                return dsn, container_id
            except Exception as exc:  # noqa: BLE001
                last_err = exc
        time.sleep(0.5)
    subprocess.run(["docker", "rm", "-f", container_id], check=False)
    raise unittest.SkipTest(f"docker postgres failed to become ready: {last_err}")


def _strip_verification(sql: str) -> str:
    if "verification helpers" in sql:
        return sql.split("-- verification helpers", 1)[0]
    return sql


@unittest.skipUnless(
    _explicitly_enabled(),
    "Postgres DSN unset and Docker unavailable/disabled "
    "(set LINKSKILLS_EPHEMERAL_PG_URL / LINKSKILLS_TEST_PG_DSN, or enable Docker)",
)
class GatewayPostgresEphemeralTests(unittest.TestCase):
    _container_id: str | None = None
    dsn: str
    psycopg: object

    @classmethod
    def setUpClass(cls) -> None:
        cls._container_id = None
        psycopg = _import_psycopg()
        if psycopg is None:
            raise unittest.SkipTest("psycopg required")
        cls.psycopg = psycopg
        dsn = _resolve_dsn()
        if dsn is None and _should_use_docker():
            dsn, cls._container_id = _start_docker_postgres()
        if not dsn:
            raise unittest.SkipTest("no postgres DSN")
        cls.dsn = dsn

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._container_id:
            subprocess.run(["docker", "rm", "-f", cls._container_id], check=False)

    def _apply_through(self, *paths: Path) -> None:
        with self.psycopg.connect(self.dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute("drop schema if exists lskills cascade;")
                cur.execute(BOOTSTRAP_SQL)
                for path in paths:
                    cur.execute(_strip_verification(path.read_text(encoding="utf-8")))
                cur.execute("grant svc_lskills_runtime to postgres;")
                cur.execute("grant svc_lskills_librarian to postgres;")
                cur.execute("grant svc_observer to postgres;")

    def setUp(self) -> None:
        self._apply_through(
            FOUNDATION_SQL,
            UPGRADE_SQL,
            GATEWAY_SQL,
            REVIEW_QUEUE_SQL,
            REVIEW_QUEUE_ACTOR_SQL,
        )

    def test_fresh_and_upgrade_paths(self) -> None:
        # Fresh: all migrations through 000009 applied in setUp — review_queue + helper.
        with self.psycopg.connect(self.dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select 1 from information_schema.tables
                    where table_schema = 'lskills' and table_name = 'review_queue'
                    """
                )
                self.assertIsNotNone(cur.fetchone())
                cur.execute(
                    """
                    select 1 from pg_proc p
                    join pg_namespace n on n.oid = p.pronamespace
                    where n.nspname = 'lskills'
                      and p.proname = 'review_queue_librarian_visible'
                    """
                )
                self.assertIsNotNone(cur.fetchone())

        # Upgrade path: stop after 000007, apply 000008, then 000009 alone.
        self._apply_through(FOUNDATION_SQL, UPGRADE_SQL, GATEWAY_SQL)
        with self.psycopg.connect(self.dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select 1 from information_schema.tables
                    where table_schema = 'lskills' and table_name = 'review_queue'
                    """
                )
                self.assertIsNone(cur.fetchone())
                cur.execute(_strip_verification(REVIEW_QUEUE_SQL.read_text(encoding="utf-8")))
                cur.execute(
                    """
                    select 1 from information_schema.tables
                    where table_schema = 'lskills' and table_name = 'review_queue'
                    """
                )
                self.assertIsNotNone(cur.fetchone())
                # Pre-000009 librarian policy is org-only; 000009 hardens to actor+org.
                cur.execute(
                    _strip_verification(REVIEW_QUEUE_ACTOR_SQL.read_text(encoding="utf-8"))
                )
                cur.execute(
                    """
                    select 1 from pg_proc p
                    join pg_namespace n on n.oid = p.pronamespace
                    where n.nspname = 'lskills'
                      and p.proname = 'review_queue_librarian_visible'
                    """
                )
                self.assertIsNotNone(cur.fetchone())
                # Re-apply is idempotent.
                cur.execute(
                    _strip_verification(REVIEW_QUEUE_ACTOR_SQL.read_text(encoding="utf-8"))
                )

    def test_idempotency_reserve_complete_replay(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        store = PostgresGatewayStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                reserved = store.reserve_idempotency("actor-a", "op", "k1", "hash-1")
                self.assertEqual(reserved.outcome, "reserved")
                self.assertIsNotNone(reserved.fence_token)
                busy = store.reserve_idempotency("actor-a", "op", "k1", "hash-1")
                self.assertEqual(busy.outcome, "in_progress")
                store.complete_idempotency(
                    "actor-a",
                    "op",
                    "k1",
                    "hash-1",
                    {"ok": True},
                    fence_token=reserved.fence_token or "",
                )
                replay = store.reserve_idempotency("actor-a", "op", "k1", "hash-1")
                self.assertEqual(replay.outcome, "replay")
                self.assertEqual(replay.envelope, {"ok": True})
                conflict = store.reserve_idempotency("actor-a", "op", "k1", "hash-2")
                self.assertEqual(conflict.outcome, "conflict")
        finally:
            store.close()

    def test_run_roundtrip_and_wrong_actor_denied(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore
        from linkskills_gateway.service import SkillRun

        run_id = str(uuid.uuid4())
        store = PostgresGatewayStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                store.save_run(
                    SkillRun(
                        run_id=run_id,
                        skill_id="demo",
                        version="1.0.0",
                        release_hash="rel",
                        profile_hash="prof",
                        actor_id="actor-a",
                        org_id="org-a",
                        status="started",
                        created_at="2026-07-30T00:00:00Z",
                        updated_at="2026-07-30T00:00:00Z",
                        events=[{"type": "run_started"}],
                    )
                )
                loaded = store.get_run(run_id)
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(loaded["actor_id"], "actor-a")
                self.assertEqual(loaded["events"][0]["type"], "run_started")

            with store.identity("actor-b", "org-a"):
                denied = store.get_run(run_id)
                self.assertIsNone(denied)

            with store.identity("actor-a", "org-b"):
                denied_org = store.get_run(run_id)
                self.assertIsNone(denied_org)
        finally:
            store.close()

    def test_atomic_idempotent_put(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        store = PostgresGatewayStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                first = store.put_idempotent(
                    "actor-a",
                    "skills_run_start",
                    "key-1",
                    {"operation": "skills_run_start", "data": {"run_id": "r1"}},
                )
                second = store.put_idempotent(
                    "actor-a",
                    "skills_run_start",
                    "key-1",
                    {"operation": "skills_run_start", "data": {"run_id": "r1"}},
                )
                self.assertEqual(first["data"]["run_id"], "r1")
                self.assertEqual(second["data"]["run_id"], "r1")
        finally:
            store.close()

    def test_rls_missing_identity_fail_closed(self) -> None:
        """Missing actor/org binding must fail closed before/at RLS write."""
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        store = PostgresGatewayStore(self.dsn, rls=True)
        try:
            with self.assertRaises(ValueError) as ctx:
                store.reserve_idempotency("actor-a", "op", "k-missing", "hash-1")
            self.assertIn("org_id", str(ctx.exception).lower())
        finally:
            store.close()

    def test_rls_cross_actor_idempotency_denied(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        store = PostgresGatewayStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                reserved = store.reserve_idempotency("actor-a", "op", "k-x", "h1")
                self.assertEqual(reserved.outcome, "reserved")
                store.complete_idempotency(
                    "actor-a",
                    "op",
                    "k-x",
                    "h1",
                    {"ok": True},
                    fence_token=reserved.fence_token or "",
                )
            with store.identity("actor-b", "org-a"):
                # Same key different actor is a distinct PK; own-row only.
                other = store.get_idempotent("actor-a", "op", "k-x")
                self.assertIsNone(other)
            with store.identity("actor-a", "org-b"):
                denied = store.get_idempotent("actor-a", "op", "k-x")
                self.assertIsNone(denied)
        finally:
            store.close()

    def test_rls_guc_cleared_after_commit_no_pool_leak(self) -> None:
        """After commit, SET LOCAL GUCs must not leak on the pooled connection."""
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        store = PostgresGatewayStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                store.reserve_idempotency("actor-a", "op", "k-leak", "h1")
            # Outside identity / after commit: session GUC should be empty.
            with store._lock:
                with store._conn.cursor() as cur:
                    cur.execute(
                        "select current_setting('app.current_actor_id', true) as actor_guc, "
                        "current_setting('app.current_org_id', true) as org_guc"
                    )
                    row = cur.fetchone()
                store._conn.commit()
            actor_guc = row["actor_guc"] if isinstance(row, dict) else row[0]
            org_guc = row["org_guc"] if isinstance(row, dict) else row[1]
            self.assertIn(actor_guc or "", ("", None))
            self.assertIn(org_guc or "", ("", None))

            # Reuse connection as another tenant — no leakage into writes.
            with store.identity("actor-b", "org-b"):
                reserved = store.reserve_idempotency("actor-b", "op", "k-leak-b", "h2")
                self.assertEqual(reserved.outcome, "reserved")
                stolen = store.get_idempotent("actor-a", "op", "k-leak")
                self.assertIsNone(stolen)
        finally:
            store.close()

    def test_atomic_run_start_update_complete_same_tenant(self) -> None:
        """Authorized same-tenant start → update → complete under RLS + nested tx."""
        from linkskills_gateway.postgres_store import PostgresGatewayStore
        from linkskills_gateway.service import SkillRun

        store = PostgresGatewayStore(self.dsn, rls=True)
        run_id = str(uuid.uuid4())
        try:
            with store.identity("actor-a", "org-a"):

                def start_mutator():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="started",
                            created_at="2026-08-03T00:00:00Z",
                            updated_at="2026-08-03T00:00:00Z",
                            events=[{"type": "run_started"}],
                        )
                    )
                    return {
                        "operation": "skills_run_start",
                        "data": {"run_id": run_id, "status": "started"},
                    }

                started = store.run_atomic_idempotent(
                    "actor-a",
                    "skills_run_start",
                    "atomic-start-1",
                    "hash-atomic-1",
                    start_mutator,
                )
                self.assertEqual(started.outcome, "replay")
                self.assertEqual(store.get_run(run_id)["status"], "started")

                def update_mutator():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="in_progress",
                            created_at="2026-08-03T00:00:00Z",
                            updated_at="2026-08-03T00:01:00Z",
                            events=[
                                {"type": "run_started"},
                                {"type": "run_update"},
                            ],
                        )
                    )
                    return {
                        "operation": "skills_run_update",
                        "data": {"run_id": run_id, "status": "in_progress"},
                    }

                updated = store.run_atomic_idempotent(
                    "actor-a",
                    "skills_run_update",
                    "atomic-update-1",
                    "hash-atomic-2",
                    update_mutator,
                )
                self.assertEqual(updated.outcome, "replay")
                self.assertEqual(store.get_run(run_id)["status"], "in_progress")

                def complete_mutator():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="completed",
                            created_at="2026-08-03T00:00:00Z",
                            updated_at="2026-08-03T00:02:00Z",
                            events=[
                                {"type": "run_started"},
                                {"type": "run_update"},
                                {"type": "run_completed"},
                            ],
                            outcome={"ok": True},
                        )
                    )
                    return {
                        "operation": "skills_run_complete",
                        "data": {"run_id": run_id, "status": "completed"},
                    }

                completed = store.run_atomic_idempotent(
                    "actor-a",
                    "skills_run_complete",
                    "atomic-complete-1",
                    "hash-atomic-3",
                    complete_mutator,
                )
                self.assertEqual(completed.outcome, "replay")
                loaded = store.get_run(run_id)
                self.assertEqual(loaded["status"], "completed")
                # Idempotent replay of start.
                replay = store.run_atomic_idempotent(
                    "actor-a",
                    "skills_run_start",
                    "atomic-start-1",
                    "hash-atomic-1",
                    start_mutator,
                )
                self.assertEqual(replay.outcome, "replay")
                self.assertEqual(replay.envelope["data"]["run_id"], run_id)
        finally:
            store.close()

    def test_atomic_rollback_clears_partial_writes_and_gucs(self) -> None:
        """Crash after nested mutation rolls back idempotency + run; GUCs clear."""
        from linkskills_gateway.postgres_store import PostgresGatewayStore
        from linkskills_gateway.service import SkillRun

        store = PostgresGatewayStore(self.dsn, rls=True)
        run_id = str(uuid.uuid4())
        try:
            with store.identity("actor-a", "org-a"):
                store._crash_after_mutation = True

                def mutator():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="started",
                            created_at="2026-08-03T00:00:00Z",
                            updated_at="2026-08-03T00:00:00Z",
                            events=[{"type": "run_started"}],
                        )
                    )
                    return {"operation": "skills_run_start", "data": {"run_id": run_id}}

                with self.assertRaises(RuntimeError):
                    store.run_atomic_idempotent(
                        "actor-a",
                        "skills_run_start",
                        "atomic-crash-1",
                        "hash-crash-1",
                        mutator,
                    )
                self.assertIsNone(store.get_run(run_id))
                self.assertIsNone(
                    store.get_idempotent("actor-a", "skills_run_start", "atomic-crash-1")
                )

            with store._lock:
                with store._conn.cursor() as cur:
                    cur.execute(
                        "select current_setting('app.current_actor_id', true) as actor_guc, "
                        "current_setting('app.current_org_id', true) as org_guc"
                    )
                    row = cur.fetchone()
                    actor_guc = row["actor_guc"] if isinstance(row, dict) else row[0]
                    org_guc = row["org_guc"] if isinstance(row, dict) else row[1]
                store._conn.commit()
            self.assertIn(actor_guc or "", ("", None))
            self.assertIn(org_guc or "", ("", None))
        finally:
            store._crash_after_mutation = False
            store.close()


    def test_gateway_schema_probe(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        store = PostgresGatewayStore(self.dsn, rls=False)
        try:
            self.assertTrue(store.probe_reachable())
            self.assertTrue(store.probe_schema_ready())
        finally:
            store.close()

    def test_review_queue_rls_wrong_actor_org_denied(self) -> None:
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True, service_scope="actor")
        try:
            with store.identity("actor-a", "org-a"):
                item = store.enqueue(
                    {
                        "review_id": "rev-a1",
                        "kind": "proposal",
                        "status": "queued",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                        "provenance": {"source": "ephemeral"},
                        "at": "2026-07-30T00:00:00Z",
                    }
                )
                self.assertEqual(item["review_id"], "rev-a1")
                self.assertEqual(store.depth(), 1)

            # Wrong actor, same org — DENIED under 000009 actor+org isolation.
            with store.identity("actor-b", "org-a"):
                listed = store.list_queue(status="queued")
                self.assertEqual(listed, [])
                self.assertEqual(store.depth(), 0)

            # Wrong org — denied.
            with store.identity("actor-a", "org-b"):
                denied = store.list_queue()
                self.assertEqual(denied, [])
                self.assertEqual(store.depth(), 0)
        finally:
            store.close()

    def test_review_queue_rls_missing_guc_denied(self) -> None:
        """Missing actor/org GUC must not expose review_queue rows."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True, service_scope="actor")
        try:
            with store.identity("actor-a", "org-a"):
                store.enqueue(
                    {
                        "review_id": "rev-guc-1",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                        "provenance": {},
                    }
                )
        finally:
            store.close()

        with self.psycopg.connect(self.dsn) as conn:  # type: ignore[attr-defined]
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute("set local role svc_lskills_librarian")
                # Intentionally omit app.current_actor_id / app.current_org_id.
                cur.execute("select count(*)::int from lskills.review_queue")
                count = cur.fetchone()[0]
            conn.rollback()
        self.assertEqual(count, 0)

        # Org GUC alone (no actor) is still denied under actor isolation.
        with self.psycopg.connect(self.dsn) as conn:  # type: ignore[attr-defined]
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute("set local role svc_lskills_librarian")
                cur.execute(
                    "select set_config('app.current_org_id', %s, true)",
                    ("org-a",),
                )
                cur.execute("select count(*)::int from lskills.review_queue")
                count_org_only = cur.fetchone()[0]
            conn.rollback()
        self.assertEqual(count_org_only, 0)

    def test_review_queue_privileged_librarian_org_scope(self) -> None:
        """Approved Librarian service_scope=org may see/claim across actors in org."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        actor_store = PostgresReviewQueueStore(
            self.dsn, rls=True, service_scope="actor"
        )
        try:
            with actor_store.identity("actor-a", "org-a"):
                actor_store.enqueue(
                    {
                        "review_id": "rev-priv-a",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                        "provenance": {"owner": "a"},
                    }
                )
            with actor_store.identity("actor-b", "org-a"):
                actor_store.enqueue(
                    {
                        "review_id": "rev-priv-b",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-b",
                        "org_id": "org-a",
                        "provenance": {"owner": "b"},
                    }
                )
                # Still denied without privileged scope.
                self.assertEqual(
                    [r["review_id"] for r in actor_store.list_queue()],
                    ["rev-priv-b"],
                )
        finally:
            actor_store.close()

        privileged = PostgresReviewQueueStore(
            self.dsn, rls=True, service_scope="org"
        )
        try:
            with privileged.identity("svc-librarian", "org-a"):
                ids = sorted(r["review_id"] for r in privileged.list_queue())
                self.assertEqual(ids, ["rev-priv-a", "rev-priv-b"])
                self.assertEqual(privileged.depth(), 2)
            # Privileged still cannot cross org boundaries.
            with privileged.identity("svc-librarian", "org-b"):
                self.assertEqual(privileged.list_queue(), [])
        finally:
            privileged.close()

    def test_review_queue_transaction_context_non_leak(self) -> None:
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                store.enqueue(
                    {
                        "review_id": "rev-ctx-a",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                        "provenance": {"source": "a"},
                    }
                )
            # New identity must not see prior org via leaked GUC.
            with store.identity("actor-z", "org-z"):
                self.assertEqual(store.list_queue(), [])
                store.enqueue(
                    {
                        "review_id": "rev-ctx-z",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-z",
                        "org_id": "org-z",
                        "provenance": {"source": "z"},
                    }
                )
                self.assertEqual(len(store.list_queue()), 1)
                self.assertEqual(store.list_queue()[0]["review_id"], "rev-ctx-z")
            with store.identity("actor-a", "org-a"):
                rows = store.list_queue()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["review_id"], "rev-ctx-a")
        finally:
            store.close()

    def test_review_queue_idempotency_and_concurrency(self) -> None:
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True)
        errors: list[BaseException] = []
        barrier = threading.Barrier(4)

        def worker(idx: int) -> None:
            try:
                barrier.wait(timeout=10)
                with store.identity("actor-a", "org-a"):
                    store.enqueue(
                        {
                            "review_id": f"rev-conc-{idx}",
                            "kind": "general",
                            "status": "queued",
                            "actor_id": "actor-a",
                            "org_id": "org-a",
                            "idempotency_key": "same-key",
                            "provenance": {"n": idx},
                        }
                    )
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(worker, range(4)))
            self.assertEqual(errors, [])
            with store.identity("actor-a", "org-a"):
                rows = store.list_queue()
                # Exactly one row for the shared idempotency key.
                keyed = [r for r in rows if r.get("idempotency_key") == "same-key"]
                self.assertEqual(len(keyed), 1)
        finally:
            store.close()

    def test_review_queue_rollback_and_recovery(self) -> None:
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                store.enqueue(
                    {
                        "review_id": "rev-fail-1",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                        "provenance": {},
                    }
                )
                # Force claim lease then expire for recovery.
                with self.psycopg.connect(self.dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            update lskills.review_queue
                            set status = 'claimed'::lskills.review_queue_status,
                                claimed_by = 'worker-1',
                                claimed_at = now() - interval '1 hour',
                                lease_expires_at = now() - interval '1 minute'
                            where review_id = 'rev-fail-1'
                            """
                        )
                recovered = store.recover_expired_leases()
                self.assertGreaterEqual(recovered, 1)
                queued = store.list_queue(status="queued")
                self.assertTrue(any(r["review_id"] == "rev-fail-1" for r in queued))

                # Retry until dead-letter.
                for _ in range(5):
                    store.mark_failed("rev-fail-1", error="boom")
                dead = store.list_queue(status="dead_letter")
                self.assertTrue(any(r["review_id"] == "rev-fail-1" for r in dead))
        finally:
            store.close()

    def test_review_queue_enqueue_rollback_on_error(self) -> None:
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True)
        try:
            with store.identity("actor-a", "org-a"):
                with self.assertRaises(Exception):
                    store.enqueue(
                        {
                            "review_id": "rev-bad-status",
                            "kind": "general",
                            "status": "not_a_real_status",
                            "actor_id": "actor-a",
                            "org_id": "org-a",
                            "provenance": {},
                        }
                    )
                self.assertEqual(store.list_queue(), [])
        finally:
            store.close()

    def test_review_queue_enqueue_rejects_forged_actor_identity(self) -> None:
        """Bound actor-a/org-a + item actor-b/org-a must fail; no row for either."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True, service_scope="actor")
        try:
            with store.identity("actor-a", "org-a"):
                with self.assertRaises(ValueError) as ctx:
                    store.enqueue(
                        {
                            "review_id": "rev-forge-actor",
                            "kind": "general",
                            "status": "queued",
                            "actor_id": "actor-b",
                            "org_id": "org-a",
                            "provenance": {"attack": "forged-actor"},
                        }
                    )
                self.assertIn("actor_id", str(ctx.exception))
                self.assertIn("disagrees", str(ctx.exception))
                self.assertIn("bound identity", str(ctx.exception))
                self.assertEqual(store.list_queue(), [])

            with store.identity("actor-b", "org-a"):
                self.assertEqual(store.list_queue(), [])
                self.assertEqual(store.depth(), 0)
            with store.identity("actor-a", "org-a"):
                self.assertEqual(store.list_queue(), [])
                self.assertEqual(store.depth(), 0)
        finally:
            store.close()

    def test_review_queue_enqueue_rejects_forged_org_identity(self) -> None:
        """Bound actor-a/org-a + item actor-a/org-b must fail; no row visible."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True, service_scope="actor")
        try:
            with store.identity("actor-a", "org-a"):
                with self.assertRaises(ValueError) as ctx:
                    store.enqueue(
                        {
                            "review_id": "rev-forge-org",
                            "kind": "general",
                            "status": "queued",
                            "actor_id": "actor-a",
                            "org_id": "org-b",
                            "provenance": {"attack": "forged-org"},
                        }
                    )
                self.assertIn("org_id", str(ctx.exception))
                self.assertIn("disagrees", str(ctx.exception))
                self.assertEqual(store.list_queue(), [])
            with store.identity("actor-a", "org-b"):
                self.assertEqual(store.list_queue(), [])
        finally:
            store.close()

    def test_review_queue_enqueue_rejects_absent_bound_identity(self) -> None:
        """Without bind_identity, enqueue fails even if item carries actor/org."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True, service_scope="actor")
        try:
            with self.assertRaises(ValueError) as ctx:
                store.enqueue(
                    {
                        "review_id": "rev-no-bind",
                        "kind": "general",
                        "status": "queued",
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                        "provenance": {},
                    }
                )
            self.assertIn("bound identity", str(ctx.exception))
            with store.identity("actor-a", "org-a"):
                self.assertEqual(store.list_queue(), [])
        finally:
            store.close()

    def test_review_queue_privileged_org_scope_rejects_forged_enqueue(self) -> None:
        """service_scope=org still requires honest bound identity on enqueue."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        privileged = PostgresReviewQueueStore(
            self.dsn, rls=True, service_scope="org"
        )
        try:
            with privileged.identity("svc-librarian", "org-a"):
                with self.assertRaises(ValueError) as ctx:
                    privileged.enqueue(
                        {
                            "review_id": "rev-priv-forge",
                            "kind": "general",
                            "status": "queued",
                            "actor_id": "actor-forged",
                            "org_id": "org-a",
                            "provenance": {},
                        }
                    )
                self.assertIn("disagrees", str(ctx.exception))
                self.assertEqual(privileged.list_queue(), [])

                # Matching / omitted identity still works under org scope.
                stamped = privileged.enqueue(
                    {
                        "review_id": "rev-priv-honest",
                        "kind": "general",
                        "status": "queued",
                        "provenance": {"ok": True},
                    }
                )
                self.assertEqual(stamped["actor_id"], "svc-librarian")
                self.assertEqual(stamped["org_id"], "org-a")
                self.assertEqual(
                    [r["review_id"] for r in privileged.list_queue()],
                    ["rev-priv-honest"],
                )
        finally:
            privileged.close()

    def test_review_queue_mutations_use_bound_identity_only(self) -> None:
        """list/mark_failed/recover use bound GUCs; forged item fields ignored."""
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        store = PostgresReviewQueueStore(self.dsn, rls=True, service_scope="actor")
        try:
            with store.identity("actor-a", "org-a"):
                store.enqueue(
                    {
                        "review_id": "rev-mut-a",
                        "kind": "general",
                        "status": "queued",
                        "provenance": {},
                    }
                )
                listed = store.list_queue()
                self.assertEqual(len(listed), 1)
                self.assertEqual(listed[0]["actor_id"], "actor-a")

                failed = store.mark_failed("rev-mut-a", error="retry-me")
                self.assertIsNotNone(failed)
                assert failed is not None
                self.assertEqual(failed["actor_id"], "actor-a")
                self.assertEqual(failed["status"], "failed")

            # Other actor cannot list or mutate via item fields (none accepted).
            with store.identity("actor-b", "org-a"):
                self.assertEqual(store.list_queue(), [])
                self.assertIsNone(store.mark_failed("rev-mut-a", error="steal"))
                self.assertEqual(store.recover_expired_leases(), 0)
        finally:
            store.close()

    def test_publisher_publish_and_get_by_hash(self) -> None:
        from linkskills_publisher.postgres_registry import PostgresPublisherRegistry

        with tempfile_skill_dir() as skill_dir:
            registry = PostgresPublisherRegistry(self.dsn, rls=True, org_id="org-pub")
            try:
                published = registry.publish_release(skill_dir, channel="internal")
                loaded = registry.get_release(published.skill_id, published.version)
                self.assertIsNotNone(loaded)
                by_hash = registry.get_by_hash(published.release_hash)
                self.assertIsNotNone(by_hash)
                assert by_hash is not None
                self.assertEqual(by_hash.bundle_hash, published.bundle_hash)
            finally:
                registry.close()


class _TempSkill:
    def __init__(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        skill = root / "demo-skill"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: demo-skill\nversion: 2.0.0\ndescription: demo\n---\n# demo\n",
            encoding="utf-8",
        )
        (skill / "references" / "eval-suite.yaml").write_text(
            "skill_id: demo-skill\nscenarios: []\n",
            encoding="utf-8",
        )
        self.path = skill

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *args: object) -> None:
        self._tmp.cleanup()


def tempfile_skill_dir() -> _TempSkill:
    return _TempSkill()


if __name__ == "__main__":
    unittest.main()
