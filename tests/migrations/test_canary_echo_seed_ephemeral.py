#!/usr/bin/env python3
"""Ephemeral Postgres apply/rollback proof for canary-echo usable seed 000010.

Never applies to stage/prod. Uses disposable Docker Postgres only.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = REPO_ROOT / "supabase" / "migrations"

CORE_SQL = MIGRATIONS / "20260715_000002_lskills_catalog_core.sql"
REGISTRY_SQL = MIGRATIONS / "20260727_000005_lskills_registry_foundation.sql"
SEED_UP = MIGRATIONS / "20260803_000010_lskills_canary_echo_usable_seed.sql"
SEED_DOWN = MIGRATIONS / "20260803_000010_lskills_canary_echo_usable_seed_down.sql"

BOOTSTRAP_SQL = """
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
"""


def _import_psycopg():
    try:
        import psycopg  # type: ignore

        return psycopg
    except ImportError:
        return None


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _should_run() -> bool:
    if os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip():
        return True
    flag = os.environ.get("LINKSKILLS_TEST_PG_DOCKER", "").strip().lower()
    if flag in {"0", "skip", "false", "no"}:
        return False
    if flag in {"1", "true", "yes", "force"}:
        return _docker_available()
    return _docker_available()


def _free_host_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_docker_postgres() -> tuple[str, str]:
    container_id = f"linkskills-canary-seed-{uuid.uuid4().hex[:8]}"
    host_port = _free_host_port()
    dsn = f"postgresql://postgres:postgres@127.0.0.1:{host_port}/linkskills_canary_seed"
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
            "POSTGRES_DB=linkskills_canary_seed",
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
        raise unittest.SkipTest("psycopg required for ephemeral canary seed tests")
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


@unittest.skipUnless(
    _should_run(),
    "Postgres DSN unset and Docker unavailable/disabled",
)
class CanaryEchoSeedEphemeralApplyTests(unittest.TestCase):
    """Apply 000010 then down on disposable Postgres; assert usable gate + cleanup."""

    @classmethod
    def setUpClass(cls) -> None:
        psycopg = _import_psycopg()
        if psycopg is None:
            raise unittest.SkipTest("psycopg required")
        cls._psycopg = psycopg
        cls._container_id = None
        env = os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip()
        if env:
            cls.dsn = env
        else:
            cls.dsn, cls._container_id = _start_docker_postgres()
        cls.conn = psycopg.connect(cls.dsn, autocommit=True)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.conn.close()
        except Exception:  # noqa: BLE001
            pass
        if cls._container_id:
            subprocess.run(["docker", "rm", "-f", cls._container_id], check=False)

    def _execute_file(self, path: Path) -> None:
        sql = path.read_text(encoding="utf-8")
        with self.conn.cursor() as cur:
            cur.execute(sql)

    def test_apply_promotes_usable_then_down_removes_only_canary_rows(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(BOOTSTRAP_SQL)
        self._execute_file(CORE_SQL)
        self._execute_file(REGISTRY_SQL)
        self._execute_file(SEED_UP)

        with self.conn.cursor() as cur:
            cur.execute(
                """
                select certification_state::text, eval_suite_ref, format_profile::text
                from lskills.catalog
                where skill_id = 'canary-echo' and version = '0.2.0'
                """
            )
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "usable")
            self.assertEqual(row[1], "skills/canary-echo/references/eval-suite.yaml")
            self.assertEqual(row[2], "simple")

            cur.execute(
                """
                select passed, overall_score, judge_tier::text
                from lskills.eval_runs
                where skill_id = 'canary-echo' and skill_version = '0.2.0'
                order by created_at desc
                limit 1
                """
            )
            ev = cur.fetchone()
            self.assertIsNotNone(ev)
            self.assertTrue(ev[0])
            self.assertEqual(float(ev[1]), 1.0)
            self.assertEqual(ev[2], "high")

            cur.execute(
                "select count(*) from lskills.releases where skill_id = 'canary-echo'"
            )
            self.assertEqual(cur.fetchone()[0], 1)
            cur.execute(
                """
                select count(*) from lskills.execution_profiles
                where profile_key = 'canary-echo-0.2.0-linux-sealed-bwrap'
                """
            )
            self.assertEqual(cur.fetchone()[0], 1)
            cur.execute(
                """
                select count(*)
                from lskills.certifications c
                join lskills.releases r on r.release_id = c.release_id
                where r.skill_id = 'canary-echo'
                """
            )
            self.assertEqual(cur.fetchone()[0], 1)

        self._execute_file(SEED_DOWN)

        with self.conn.cursor() as cur:
            cur.execute(
                "select count(*) from lskills.catalog where skill_id = 'canary-echo'"
            )
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute(
                "select count(*) from lskills.eval_runs where skill_id = 'canary-echo'"
            )
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute(
                "select count(*) from lskills.releases where skill_id = 'canary-echo'"
            )
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute(
                """
                select count(*) from lskills.execution_profiles
                where profile_key = 'canary-echo-0.2.0-linux-sealed-bwrap'
                """
            )
            self.assertEqual(cur.fetchone()[0], 0)
            # Core schema still present after down (no drop schema).
            cur.execute(
                """
                select count(*) from information_schema.tables
                where table_schema = 'lskills'
                  and table_name in ('catalog', 'eval_runs', 'releases')
                """
            )
            self.assertEqual(cur.fetchone()[0], 3)


if __name__ == "__main__":
    unittest.main()
