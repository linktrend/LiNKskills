#!/usr/bin/env python3
"""Ephemeral Postgres apply/rollback proof for canary-echo usable seed 000010.

Never applies to stage/prod. Uses disposable Docker Postgres only.

Covers:
  - happy-path apply + scoped down
  - fail-closed up when pre-existing rows mismatch pinned IDs/hashes
  - down deletes only exact package IDs/hashes (leaves later legitimate rows)
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

# Pinned package constants (must match migration header; parent may refresh later).
PKG_EVAL_RUN_ID = "c4e00010-a001-4000-8000-c4a47ee00001"
PKG_RELEASE_ID = "c4e00010-a002-4000-8000-c4a47ee00001"
PKG_PROFILE_ID = "c4e00010-a003-4000-8000-c4a47ee00001"
PKG_CERT_ID = "c4e00010-a004-4000-8000-c4a47ee00001"
PKG_RELEASE_HASH = (
    "skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb"
)
PKG_PROFILE_HASH = "9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188"
PKG_SUITE_HASH = "8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662"
PKG_EVIDENCE_HASH = "a0bb2d56703cb95a6766a8902176f613dffed6af39d798546b338c5b3d77c262"
PKG_PROFILE_KEY = "canary-echo-0.2.0-linux-sealed-bwrap"
PKG_EVAL_SUITE_REF = "skills/canary-echo/references/eval-suite.yaml"
PKG_TOOL_HASH = "29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83"

# Distinct "later legitimate" pins — must NOT match package constants.
LATER_EVAL_RUN_ID = "d5f11111-b111-4111-8111-d5b11ee11111"
LATER_RELEASE_ID = "d5f11111-b222-4222-8222-d5b11ee22222"
LATER_PROFILE_ID = "d5f11111-b333-4333-8333-d5b11ee33333"
LATER_CERT_ID = "d5f11111-b444-4444-8444-d5b11ee44444"
LATER_RELEASE_HASH = (
    "skill-release:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
LATER_PROFILE_HASH = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
LATER_EVIDENCE_HASH = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
LATER_PROFILE_KEY = "canary-echo-0.2.0-linux-sealed-later"

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

    def setUp(self) -> None:
        """Reset lskills schema so each case starts from foundation only."""
        with self.conn.cursor() as cur:
            cur.execute("drop schema if exists lskills cascade")
        with self.conn.cursor() as cur:
            cur.execute(BOOTSTRAP_SQL)
        self._execute_sql_file(CORE_SQL)
        self._execute_sql_file(REGISTRY_SQL)

    def _execute_sql_file(self, path: Path) -> None:
        """Apply SQL file in one transaction (atomic like Platform migrate)."""
        sql = path.read_text(encoding="utf-8")
        self.conn.autocommit = False
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            self.conn.autocommit = True

    def _execute_sql_file_expect_fail(self, path: Path) -> BaseException:
        """Apply SQL expecting RAISE EXCEPTION; return the error after rollback."""
        sql = path.read_text(encoding="utf-8")
        self.conn.autocommit = False
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit()
            self.fail(f"expected {path.name} to fail closed, but it committed")
        except Exception as exc:  # noqa: BLE001
            self.conn.rollback()
            return exc
        finally:
            self.conn.autocommit = True

    def _count(self, sql: str, params: tuple | None = None) -> int:
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return int(cur.fetchone()[0])

    def _insert_wrong_catalog_draft(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.catalog (
                  skill_id, version, org_id, display_name, description,
                  format_profile, frontmatter, disclosure_refs, eval_suite_ref,
                  certification_state, min_reasoning_tier
                ) values (
                  'canary-echo', '0.2.0', null, 'canary-echo-WRONG', 'wrong row',
                  'simple',
                  jsonb_build_object(
                    'skill_release_hash', (%s)::text,
                    'profile_hash', '0000000000000000000000000000000000000000000000000000000000000000',
                    'suite_hash', '1111111111111111111111111111111111111111111111111111111111111111',
                    'sealed_evidence_sha256', '2222222222222222222222222222222222222222222222222222222222222222'
                  ),
                  '{}'::jsonb,
                  (%s)::text,
                  'draft',
                  'fast'
                )
                """,
                (LATER_RELEASE_HASH, PKG_EVAL_SUITE_REF),
            )

    def _insert_wrong_release(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.releases (
                  release_id, skill_id, version, release_hash, channel,
                  content_manifest, immutable, metadata
                ) values (
                  (%s)::uuid, 'canary-echo', '0.2.0', (%s)::text, 'canary',
                  '{}'::jsonb, true, '{}'::jsonb
                )
                """,
                (LATER_RELEASE_ID, LATER_RELEASE_HASH),
            )

    def _insert_wrong_profile(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.execution_profiles (
                  profile_id, profile_key, profile_hash, runtime,
                  adapter_version, toolchain, metadata
                ) values (
                  (%s)::uuid, (%s)::text, (%s)::text, 'linux',
                  'wrong-adapter', '{}'::jsonb, '{}'::jsonb
                )
                """,
                (LATER_PROFILE_ID, PKG_PROFILE_KEY, LATER_PROFILE_HASH),
            )

    def _insert_wrong_eval_run(self) -> None:
        """Conflict on package eval_run_id with wrong evidence hashes."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.eval_runs (
                  eval_run_id, skill_id, skill_version, eval_suite_ref,
                  rubric_scores, overall_score, passed, pass_threshold,
                  efficiency_metrics, size_metrics,
                  judge_model, judge_model_version, judge_tier
                ) values (
                  (%s)::uuid, 'canary-echo', '0.2.0', (%s)::text,
                  '{"correctness": 0.5}'::jsonb, 0.5, true, 0.8,
                  jsonb_build_object(
                    'sealed_evidence_sha256', (%s)::text,
                    'skill_release_hash', (%s)::text,
                    'profile_hash', (%s)::text,
                    'suite_hash', (%s)::text
                  ),
                  '{}'::jsonb,
                  'wrong-judge', 'wrong/0.0.0', 'high'
                )
                """,
                (
                    PKG_EVAL_RUN_ID,
                    PKG_EVAL_SUITE_REF,
                    LATER_EVIDENCE_HASH,
                    LATER_RELEASE_HASH,
                    LATER_PROFILE_HASH,
                    "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
                ),
            )

    def _insert_later_legitimate_package(self) -> None:
        """Insert a full canary-echo 0.2.0 graph with non-package IDs/hashes."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.catalog (
                  skill_id, version, org_id, display_name, description,
                  format_profile, frontmatter, disclosure_refs, eval_suite_ref,
                  certification_state, min_reasoning_tier
                ) values (
                  'canary-echo', '0.2.0', null, 'canary-echo-later', 'later legitimate',
                  'simple',
                  jsonb_build_object(
                    'skill_release_hash', (%s)::text,
                    'profile_hash', (%s)::text,
                    'suite_hash', 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
                    'sealed_evidence_sha256', (%s)::text
                  ),
                  '{}'::jsonb,
                  (%s)::text,
                  'draft',
                  'fast'
                )
                """,
                (
                    LATER_RELEASE_HASH,
                    LATER_PROFILE_HASH,
                    LATER_EVIDENCE_HASH,
                    PKG_EVAL_SUITE_REF,
                ),
            )
            cur.execute(
                """
                insert into lskills.eval_runs (
                  eval_run_id, skill_id, skill_version, eval_suite_ref,
                  rubric_scores, overall_score, passed, pass_threshold,
                  efficiency_metrics, size_metrics,
                  judge_model, judge_model_version, judge_tier
                ) values (
                  (%s)::uuid, 'canary-echo', '0.2.0', (%s)::text,
                  '{"correctness": 1.0}'::jsonb, 1.0, true, 0.8,
                  jsonb_build_object('sealed_evidence_sha256', (%s)::text),
                  '{}'::jsonb,
                  'later-judge', 'later/1.0.0', 'high'
                )
                """,
                (LATER_EVAL_RUN_ID, PKG_EVAL_SUITE_REF, LATER_EVIDENCE_HASH),
            )
            cur.execute(
                """
                update lskills.catalog
                set certification_state = 'usable', updated_at = now()
                where skill_id = 'canary-echo' and version = '0.2.0'
                """
            )
            cur.execute(
                """
                insert into lskills.releases (
                  release_id, skill_id, version, release_hash, channel,
                  content_manifest, immutable, metadata
                ) values (
                  (%s)::uuid, 'canary-echo', '0.2.0', (%s)::text, 'canary',
                  '{}'::jsonb, true, jsonb_build_object('package', 'later-legitimate')
                )
                """,
                (LATER_RELEASE_ID, LATER_RELEASE_HASH),
            )
            cur.execute(
                """
                insert into lskills.execution_profiles (
                  profile_id, profile_key, profile_hash, runtime,
                  adapter_version, toolchain, metadata
                ) values (
                  (%s)::uuid, (%s)::text, (%s)::text, 'linux',
                  'later-adapter', '{}'::jsonb, '{}'::jsonb
                )
                """,
                (LATER_PROFILE_ID, LATER_PROFILE_KEY, LATER_PROFILE_HASH),
            )
            cur.execute(
                """
                insert into lskills.certifications (
                  certification_id, release_id, profile_id, eval_run_ref,
                  evidence_hash, state, certified_at, metadata
                ) values (
                  (%s)::uuid, (%s)::uuid, (%s)::uuid, (%s)::text,
                  (%s)::text, 'usable', now(), '{}'::jsonb
                )
                """,
                (
                    LATER_CERT_ID,
                    LATER_RELEASE_ID,
                    LATER_PROFILE_ID,
                    PKG_EVAL_SUITE_REF,
                    LATER_EVIDENCE_HASH,
                ),
            )

    def test_apply_promotes_usable_then_down_removes_only_canary_rows(self) -> None:
        self._execute_sql_file(SEED_UP)

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
            self.assertEqual(row[1], PKG_EVAL_SUITE_REF)
            self.assertEqual(row[2], "simple")

            cur.execute(
                """
                select passed, overall_score, judge_tier::text, eval_run_id::text
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
            self.assertEqual(ev[3], PKG_EVAL_RUN_ID)

            cur.execute(
                """
                select release_id::text, release_hash
                from lskills.releases where skill_id = 'canary-echo'
                """
            )
            rel = cur.fetchone()
            self.assertEqual(rel[0], PKG_RELEASE_ID)
            self.assertEqual(rel[1], PKG_RELEASE_HASH)

            cur.execute(
                """
                select profile_id::text, profile_hash from lskills.execution_profiles
                where profile_key = %s
                """,
                (PKG_PROFILE_KEY,),
            )
            prof = cur.fetchone()
            self.assertEqual(prof[0], PKG_PROFILE_ID)
            self.assertEqual(prof[1], PKG_PROFILE_HASH)

            cur.execute(
                """
                select certification_id::text, evidence_hash
                from lskills.certifications where certification_id = %s::uuid
                """,
                (PKG_CERT_ID,),
            )
            cert = cur.fetchone()
            self.assertEqual(cert[0], PKG_CERT_ID)
            self.assertEqual(cert[1], PKG_EVIDENCE_HASH)

        self._execute_sql_file(SEED_DOWN)

        self.assertEqual(
            self._count("select count(*) from lskills.catalog where skill_id = 'canary-echo'"),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.eval_runs where skill_id = 'canary-echo'"
            ),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.releases where skill_id = 'canary-echo'"
            ),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.execution_profiles where profile_key = %s",
                (PKG_PROFILE_KEY,),
            ),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.certifications where certification_id = %s::uuid",
                (PKG_CERT_ID,),
            ),
            0,
        )
        # Core schema still present after down (no drop schema).
        self.assertEqual(
            self._count(
                """
                select count(*) from information_schema.tables
                where table_schema = 'lskills'
                  and table_name in ('catalog', 'eval_runs', 'releases')
                """
            ),
            3,
        )

    def test_idempotent_reapply_when_exact_package_rows_present(self) -> None:
        self._execute_sql_file(SEED_UP)
        self._execute_sql_file(SEED_UP)  # second apply must succeed (exact match)
        self.assertEqual(
            self._count(
                """
                select count(*) from lskills.catalog
                where skill_id = 'canary-echo' and version = '0.2.0'
                  and certification_state = 'usable'
                """
            ),
            1,
        )

    def test_fail_closed_wrong_catalog_rolls_back_no_usable(self) -> None:
        self._insert_wrong_catalog_draft()
        err = self._execute_sql_file_expect_fail(SEED_UP)
        self.assertIn("fail-closed", str(err).lower())

        with self.conn.cursor() as cur:
            cur.execute(
                """
                select certification_state::text, display_name
                from lskills.catalog
                where skill_id = 'canary-echo' and version = '0.2.0'
                """
            )
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "draft")  # not promoted
            self.assertEqual(row[1], "canary-echo-WRONG")  # preinsert untouched
            cur.execute(
                """
                select count(*) from lskills.eval_runs
                where eval_run_id = %s::uuid
                """,
                (PKG_EVAL_RUN_ID,),
            )
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute(
                """
                select count(*) from lskills.releases
                where release_id = %s::uuid
                """,
                (PKG_RELEASE_ID,),
            )
            self.assertEqual(cur.fetchone()[0], 0)

    def _insert_matching_catalog_draft(self) -> None:
        """Preinsert catalog that matches package pins (still draft)."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.catalog (
                  skill_id, version, org_id, display_name, description,
                  format_profile, frontmatter, disclosure_refs, eval_suite_ref,
                  certification_state, min_reasoning_tier
                ) values (
                  'canary-echo', '0.2.0', null, 'canary-echo',
                  'Stage lifecycle canary that echoes tokens via packaged text-echo under sealed Eval Runner certification. No durable shared/repo/network side effects; workspace-scoped tool writes and mandatory ledger telemetry only.',
                  'simple',
                  jsonb_build_object(
                    'name', 'canary-echo',
                    'version', '0.2.0',
                    'format_profile', 'simple',
                    'release_tag', 'v0.2.0',
                    'sealed_evidence_path', 'evidence/phase10/sealed/canary-echo-sealed.json',
                    'skill_release_hash', (%s)::text,
                    'profile_hash', (%s)::text,
                    'suite_hash', (%s)::text,
                    'sealed_evidence_sha256', (%s)::text
                  ),
                  jsonb_build_object(
                    'advanced', 'skills/canary-echo/advanced/advanced.md',
                    'schemas', 'skills/canary-echo/references/schemas.json'
                  ),
                  (%s)::text,
                  'draft',
                  'fast'
                )
                """,
                (
                    PKG_RELEASE_HASH,
                    PKG_PROFILE_HASH,
                    PKG_SUITE_HASH,
                    PKG_EVIDENCE_HASH,
                    PKG_EVAL_SUITE_REF,
                ),
            )

    def test_fail_closed_wrong_release_rolls_back(self) -> None:
        # Matching catalog so fail-closed triggers on release pins, not catalog.
        self._insert_matching_catalog_draft()
        self._insert_wrong_release()
        err = self._execute_sql_file_expect_fail(SEED_UP)
        self.assertIn("fail-closed", str(err).lower())
        self.assertIn("releases", str(err).lower())
        self.assertEqual(
            self._count(
                "select count(*) from lskills.releases where release_id = %s::uuid",
                (PKG_RELEASE_ID,),
            ),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.releases where release_id = %s::uuid",
                (LATER_RELEASE_ID,),
            ),
            1,
        )
        # Catalog must not have been promoted by a partial apply.
        with self.conn.cursor() as cur:
            cur.execute(
                """
                select certification_state::text from lskills.catalog
                where skill_id = 'canary-echo' and version = '0.2.0'
                """
            )
            self.assertEqual(cur.fetchone()[0], "draft")
            cur.execute(
                """
                select count(*) from lskills.eval_runs
                where eval_run_id = %s::uuid
                """,
                (PKG_EVAL_RUN_ID,),
            )
            self.assertEqual(cur.fetchone()[0], 0)

    def test_fail_closed_wrong_profile_rolls_back(self) -> None:
        self._insert_matching_catalog_draft()
        self._insert_wrong_profile()
        err = self._execute_sql_file_expect_fail(SEED_UP)
        self.assertIn("fail-closed", str(err).lower())
        self.assertIn("execution_profiles", str(err).lower())
        self.assertEqual(
            self._count(
                "select count(*) from lskills.execution_profiles where profile_id = %s::uuid",
                (PKG_PROFILE_ID,),
            ),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.execution_profiles where profile_id = %s::uuid",
                (LATER_PROFILE_ID,),
            ),
            1,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.releases where release_id = %s::uuid",
                (PKG_RELEASE_ID,),
            ),
            0,
        )

    def test_fail_closed_wrong_eval_run_rolls_back(self) -> None:
        self._insert_wrong_eval_run()
        err = self._execute_sql_file_expect_fail(SEED_UP)
        self.assertIn("fail-closed", str(err).lower())
        with self.conn.cursor() as cur:
            cur.execute(
                """
                select efficiency_metrics->>'sealed_evidence_sha256'
                from lskills.eval_runs where eval_run_id = %s::uuid
                """,
                (PKG_EVAL_RUN_ID,),
            )
            self.assertEqual(cur.fetchone()[0], LATER_EVIDENCE_HASH)
            cur.execute(
                """
                select count(*) from lskills.catalog
                where skill_id = 'canary-echo' and certification_state = 'usable'
                """
            )
            self.assertEqual(cur.fetchone()[0], 0)

    def test_down_leaves_later_legitimate_rows_intact(self) -> None:
        self._insert_later_legitimate_package()
        self._execute_sql_file(SEED_DOWN)

        self.assertEqual(
            self._count(
                """
                select count(*) from lskills.catalog
                where skill_id = 'canary-echo' and version = '0.2.0'
                  and frontmatter->>'skill_release_hash' = %s
                """,
                (LATER_RELEASE_HASH,),
            ),
            1,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.eval_runs where eval_run_id = %s::uuid",
                (LATER_EVAL_RUN_ID,),
            ),
            1,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.releases where release_id = %s::uuid",
                (LATER_RELEASE_ID,),
            ),
            1,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.execution_profiles where profile_id = %s::uuid",
                (LATER_PROFILE_ID,),
            ),
            1,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.certifications where certification_id = %s::uuid",
                (LATER_CERT_ID,),
            ),
            1,
        )

    def test_down_after_apply_does_not_delete_extra_eval_run(self) -> None:
        self._execute_sql_file(SEED_UP)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                insert into lskills.eval_runs (
                  eval_run_id, skill_id, skill_version, eval_suite_ref,
                  rubric_scores, overall_score, passed, pass_threshold,
                  efficiency_metrics, size_metrics,
                  judge_model, judge_model_version, judge_tier
                ) values (
                  %s::uuid, 'canary-echo', '0.2.0', %s,
                  '{"correctness": 1.0}'::jsonb, 1.0, true, 0.8,
                  jsonb_build_object('note', 'later-extra'),
                  '{}'::jsonb,
                  'extra-judge', 'extra/1.0.0', 'high'
                )
                """,
                (LATER_EVAL_RUN_ID, PKG_EVAL_SUITE_REF),
            )
        self._execute_sql_file(SEED_DOWN)
        self.assertEqual(
            self._count(
                "select count(*) from lskills.eval_runs where eval_run_id = %s::uuid",
                (PKG_EVAL_RUN_ID,),
            ),
            0,
        )
        self.assertEqual(
            self._count(
                "select count(*) from lskills.eval_runs where eval_run_id = %s::uuid",
                (LATER_EVAL_RUN_ID,),
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
