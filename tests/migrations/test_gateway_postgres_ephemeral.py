#!/usr/bin/env python3
"""Ephemeral Postgres proofs for GatewayStore Postgres adapter + RLS.

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
import time
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "librarian_domain"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))

MIGRATIONS = REPO_ROOT / "supabase" / "migrations"
FOUNDATION_SQL = MIGRATIONS / "20260727_000005_lskills_registry_foundation.sql"
UPGRADE_SQL = MIGRATIONS / "20260728_000006_lskills_rls_actor_org_scope.sql"
GATEWAY_SQL = MIGRATIONS / "20260730_000007_lskills_gateway_persistence.sql"
REVIEW_QUEUE_DDL = REPO_ROOT / "tests" / "helpers" / "ephemeral_review_queue_ddl.sql"

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

    def setUp(self) -> None:
        with self.psycopg.connect(self.dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute("drop schema if exists lskills cascade;")
                cur.execute(BOOTSTRAP_SQL)
                for path in (FOUNDATION_SQL, UPGRADE_SQL, GATEWAY_SQL):
                    cur.execute(_strip_verification(path.read_text(encoding="utf-8")))
                # Allow tests to SET ROLE to service roles.
                cur.execute("grant svc_lskills_runtime to postgres;")
                cur.execute("grant svc_lskills_librarian to postgres;")

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

    def test_librarian_review_queue_ephemeral_ddl(self) -> None:
        from linkskills_librarian.postgres_store import PostgresReviewQueueStore

        with self.psycopg.connect(self.dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(REVIEW_QUEUE_DDL.read_text(encoding="utf-8"))

        store = PostgresReviewQueueStore(self.dsn)
        try:
            item = {
                "review_id": "rev-1",
                "kind": "proposal",
                "status": "queued",
                "at": "2026-07-30T00:00:00Z",
            }
            store.enqueue(item)
            self.assertEqual(store.depth(), 1)
            queued = store.list_queue(status="queued")
            self.assertEqual(len(queued), 1)
            self.assertEqual(queued[0]["review_id"], "rev-1")
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
