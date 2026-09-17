#!/usr/bin/env python3
"""Ephemeral PostgreSQL 17 proofs for the production store package.

Uses a disposable data directory owned by the current user. Never prints a DSN,
never uses production credentials, and never applies to a shared database.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "persistence"))

from linkskills_persistence.migration_package import load_manifest, verify_manifest_files
from linkskills_persistence.readiness import diagnose_snapshot, diagnose_store_exception

PG_BIN = Path("/usr/lib/postgresql/17/bin")
MIGRATIONS = REPO_ROOT / "supabase" / "migrations"

PLATFORM_BOOTSTRAP = """
create extension if not exists "pgcrypto";
create schema if not exists platform;
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
create or replace function platform.has_org_access(org uuid, min_role platform.member_role)
returns boolean language sql stable as $$ select true $$;
do $$
begin
  -- Platform-owned PostgREST principal names only. NOLOGIN, no password, no secret.
  if not exists (select 1 from pg_roles where rolname = 'service_role') then
    create role service_role nologin nobypassrls;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticator') then
    create role authenticator nologin nobypassrls;
  end if;
end $$;
"""


def _import_psycopg():
    try:
        import psycopg

        return psycopg
    except ImportError:
        return None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class _EphemeralPG17:
    """Start PostgreSQL 17 on loopback with trust auth for this process only."""

    def __init__(self) -> None:
        self.data_dir = Path(tempfile.mkdtemp(prefix="lskills-ed01-pg17-"))
        self.port = _free_port()
        self.psycopg = _import_psycopg()
        if self.psycopg is None:
            shutil.rmtree(self.data_dir, ignore_errors=True)
            raise unittest.SkipTest("psycopg required for ephemeral PostgreSQL 17 tests")
        if not (PG_BIN / "initdb").is_file():
            shutil.rmtree(self.data_dir, ignore_errors=True)
            raise unittest.SkipTest("PostgreSQL 17 binaries are required")
        init = subprocess.run(
            [
                str(PG_BIN / "initdb"),
                "-D",
                str(self.data_dir),
                "--auth=trust",
                "--username=ed01",
                "--no-sync",
                "--encoding=UTF8",
                "--locale=C.UTF-8",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if init.returncode != 0:
            shutil.rmtree(self.data_dir, ignore_errors=True)
            raise unittest.SkipTest("initdb failed for ephemeral PostgreSQL 17")
        log_file = self.data_dir / "pg.log"
        started = subprocess.run(
            [
                str(PG_BIN / "pg_ctl"),
                "-D",
                str(self.data_dir),
                "-l",
                str(log_file),
                "-o",
                f"-p {self.port} -h 127.0.0.1 -k {self.data_dir}",
                "start",
                "-w",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if started.returncode != 0:
            shutil.rmtree(self.data_dir, ignore_errors=True)
            raise unittest.SkipTest("pg_ctl start failed for ephemeral PostgreSQL 17")
        self._wait_ready()

    def _wait_ready(self) -> None:
        last = None
        for _ in range(40):
            try:
                with self.psycopg.connect(
                    host=str(self.data_dir),
                    port=self.port,
                    dbname="postgres",
                    user="ed01",
                    client_encoding="UTF8",
                ) as conn:
                    with conn.cursor() as cur:
                        cur.execute("select current_setting('server_version')")
                        self.server_version = str(cur.fetchone()[0])
                    conn.commit()
                return
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(0.15)
        self.stop()
        raise unittest.SkipTest(f"ephemeral PostgreSQL 17 did not become ready: {type(last).__name__}")

    def connect(self):
        return self.psycopg.connect(
            host=str(self.data_dir),
            port=self.port,
            dbname="postgres",
            user="ed01",
            client_encoding="UTF8",
        )

    def exec_sql(self, sql: str) -> None:
        with self.connect() as conn:
            conn.execute(sql)
            conn.commit()

    def exec_file(self, path: Path) -> None:
        self.exec_sql(path.read_text(encoding="utf-8"))

    def stop(self) -> None:
        subprocess.run(
            [str(PG_BIN / "pg_ctl"), "-D", str(self.data_dir), "-m", "immediate", "stop"],
            capture_output=True,
            check=False,
        )
        shutil.rmtree(self.data_dir, ignore_errors=True)


def _ordered_ups(manifest: dict) -> list[Path]:
    return [REPO_ROOT / entry["up"] for entry in sorted(manifest["entries"], key=lambda e: int(e["order"]))]


class ProductionStoreEphemeralPg17Tests(unittest.TestCase):
    cluster: _EphemeralPG17 | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest(REPO_ROOT)
        verify_manifest_files(REPO_ROOT, cls.manifest)
        cls.cluster = _EphemeralPG17()
        cls.cluster.exec_sql(PLATFORM_BOOTSTRAP)
        for path in _ordered_ups(cls.manifest):
            try:
                cls.cluster.exec_file(path)
            except Exception as exc:
                from linkskills_persistence.readiness import redact_store_text

                detail = redact_store_text(f"{type(exc).__name__}: {exc}")
                cls.cluster.stop()
                cls.cluster = None
                raise RuntimeError(f"apply failed at {path.name}: {detail}") from exc

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.cluster is not None:
            cls.cluster.stop()
            cls.cluster = None

    def test_postgres_major_is_17(self) -> None:
        self.assertIsNotNone(self.cluster)
        self.assertTrue(self.cluster.server_version.startswith("17."), self.cluster.server_version)

    def test_snapshot_ready_under_runtime_role(self) -> None:
        with self.cluster.connect() as conn:
            conn.execute("set role svc_lskills_runtime")
            row = conn.execute("select lskills.store_readiness_snapshot()").fetchone()[0]
            conn.rollback()
        diagnostic = diagnose_snapshot(row)
        self.assertTrue(row["ready"])
        self.assertEqual(row["missing_relations"], [])
        self.assertEqual(row["postgres_major"], 17)
        self.assertFalse(row["live_apply"])
        self.assertTrue(diagnostic["ready"])
        self.assertEqual(
            diagnostic["payload_digest_sha256"],
            self.manifest["payload_digest_sha256"],
        )

    def test_runtime_cannot_write_store_package(self) -> None:
        with self.cluster.connect() as conn:
            conn.execute("set role svc_lskills_runtime")
            try:
                conn.execute(
                    "insert into lskills.store_package "
                    "(package_id, package_version, payload_digest_sha256) "
                    "values (%s, %s, %s)",
                    (f"probe-{uuid.uuid4()}", "9.9.9", "a" * 64),
                )
                conn.commit()
                self.fail("runtime insert into store_package must fail closed")
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                diagnosis = diagnose_store_exception(exc)
                self.assertFalse(diagnosis["ready"])
                self.assertEqual(diagnosis["code"], "store_privilege_denied")
                dumped = str(diagnosis).lower()
                self.assertNotIn("password", dumped)
                self.assertNotIn("postgresql://", dumped)

    def test_runtime_rls_blocks_unbound_gateway_insert(self) -> None:
        with self.cluster.connect() as conn:
            conn.execute("set role svc_lskills_runtime")
            try:
                conn.execute(
                    "insert into lskills.idempotency "
                    "(actor_id, org_id, operation, idempotency_key, request_hash) "
                    "values (%s, %s, %s, %s, %s)",
                    ("actor-a", "org-a", "skills_run_start", "key-1", "hash-1"),
                )
                conn.commit()
                self.fail("unbound runtime insert must fail closed under RLS")
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                self.assertEqual(diagnose_store_exception(exc)["code"], "store_privilege_denied")

    def test_runtime_can_insert_idempotency_with_gucs_and_replay(self) -> None:
        actor = str(uuid.uuid4())
        org = str(uuid.uuid4())
        key = f"idem-{uuid.uuid4()}"
        with self.cluster.connect() as conn:
            conn.execute("set role svc_lskills_runtime")
            conn.execute("select set_config('app.current_actor_id', %s, true)", (actor,))
            conn.execute("select set_config('app.current_org_id', %s, true)", (org,))
            conn.execute(
                "insert into lskills.idempotency "
                "(actor_id, org_id, operation, idempotency_key, request_hash) "
                "values (%s, %s, %s, %s, %s)",
                (actor, org, "skills_run_start", key, "hash-1"),
            )
            conn.commit()
        with self.cluster.connect() as conn:
            conn.execute("set role svc_lskills_runtime")
            conn.execute("select set_config('app.current_actor_id', %s, true)", (actor,))
            conn.execute("select set_config('app.current_org_id', %s, true)", (org,))
            conn.execute(
                "insert into lskills.idempotency "
                "(actor_id, org_id, operation, idempotency_key, request_hash) "
                "values (%s, %s, %s, %s, %s) "
                "on conflict (actor_id, operation, idempotency_key) do nothing",
                (actor, org, "skills_run_start", key, "hash-1"),
            )
            count = conn.execute(
                "select count(*) from lskills.idempotency "
                "where actor_id = %s and idempotency_key = %s",
                (actor, key),
            ).fetchone()[0]
            conn.commit()
        self.assertEqual(int(count), 1)

    def test_binder_reapply_is_idempotent(self) -> None:
        binder = MIGRATIONS / "20260910_000013_lskills_production_store_readiness.sql"
        self.cluster.exec_file(binder)
        with self.cluster.connect() as conn:
            count = conn.execute(
                "select count(*) from lskills.store_package "
                "where package_id = 'lskills-production-store-readiness'"
            ).fetchone()[0]
            conn.commit()
        self.assertEqual(int(count), 1)

    def test_down_then_up_restores_binder(self) -> None:
        down = MIGRATIONS / "20260910_000013_lskills_production_store_readiness_down.sql"
        up = MIGRATIONS / "20260910_000013_lskills_production_store_readiness.sql"
        self.cluster.exec_file(down)
        with self.cluster.connect() as conn:
            missing = conn.execute(
                "select to_regclass('lskills.store_package') is null"
            ).fetchone()[0]
            conn.commit()
        self.assertTrue(missing)
        self.cluster.exec_file(up)
        with self.cluster.connect() as conn:
            conn.execute("set role svc_lskills_runtime")
            ready = conn.execute("select lskills.store_readiness_snapshot()").fetchone()[0]["ready"]
            conn.rollback()
        self.assertTrue(ready)


if __name__ == "__main__":
    unittest.main()
