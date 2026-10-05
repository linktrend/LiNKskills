"""Focused real-Postgres drift regression; requires an explicit empty test DB."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

try:
    import psycopg
except ImportError:
    psycopg = None

DSN = os.environ.get("LINKSKILLS_QUARANTINE_TEST_PG_URL", "")
DISPOSABLE = os.environ.get("LINKSKILLS_QUARANTINE_ALLOW_DISPOSABLE_DB") == "1"
MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase/migrations/20261005_000015_lskills_registry_quarantine.sql"
)


@unittest.skipUnless(psycopg and DSN and DISPOSABLE, "explicit disposable PostgreSQL required")
class QuarantineConstraintPostgresTests(unittest.TestCase):
    """Never connects using production/default publisher credential variables."""

    def setUp(self):
        self.conn = psycopg.connect(DSN)
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        with self.conn.cursor() as cur:
            cur.execute("select current_database(), to_regnamespace('lskills')")
            database, existing_schema = cur.fetchone()
            if not database.startswith("lskills_quarantine_test_") or existing_schema is not None:
                self.fail("Requires an empty lskills_quarantine_test_* disposable database")
            cur.execute("""
                do $$ begin
                  if not exists (select 1 from pg_roles where rolname='svc_lskills_runtime') then
                    create role svc_lskills_runtime nologin;
                  end if;
                end $$;
                create schema lskills;
                create function lskills.require_org_context() returns boolean language sql
                  as 'select nullif(current_setting(''app.current_org_id'', true), '''') is not null';
                create table lskills.releases (release_id uuid primary key);
                create table lskills.bundles (release_id uuid references lskills.releases);
            """)

    def add_existing_constraint(self, expression, *, validated=True):
        with self.conn.cursor() as cur:
            cur.execute("alter table lskills.releases add column registry_lifecycle text not null default 'published'")
            # Expressions are fixed synthetic test literals, never caller input.
            suffix = "" if validated else " not valid"
            cur.execute(f"alter table lskills.releases add constraint lifecycle_check check ({expression}){suffix}")

    def apply(self):
        with self.conn.cursor() as cur:
            cur.execute(MIGRATION.read_text(encoding="utf-8"))

    def test_fresh_column_and_exact_second_apply(self):
        self.apply()
        self.apply()

    def test_exact_existing_constraint(self):
        self.add_existing_constraint("registry_lifecycle in ('quarantined','published','retired')")
        self.apply()
        self.apply()

    def test_published_only_rejected(self):
        self.add_existing_constraint("registry_lifecycle in ('published')")
        with self.assertRaisesRegex(psycopg.errors.RaiseException, "allowed-values"):
            self.apply()

    def test_extra_allowed_value_rejected(self):
        self.add_existing_constraint("registry_lifecycle in ('quarantined','published','retired','unexpected')")
        with self.assertRaisesRegex(psycopg.errors.RaiseException, "allowed-values"):
            self.apply()

    def test_same_words_wrong_semantics_rejected(self):
        self.add_existing_constraint("registry_lifecycle not in ('quarantined','published','retired')")
        with self.assertRaisesRegex(psycopg.errors.RaiseException, "allowed-values"):
            self.apply()

    def test_unvalidated_constraint_rejected(self):
        self.add_existing_constraint("registry_lifecycle in ('quarantined','published','retired')", validated=False)
        with self.assertRaisesRegex(psycopg.errors.RaiseException, "allowed-values"):
            self.apply()

    def test_conflicting_second_constraint_rejected(self):
        self.add_existing_constraint("registry_lifecycle in ('quarantined','published','retired')")
        with self.conn.cursor() as cur:
            cur.execute("alter table lskills.releases add constraint published_only check (registry_lifecycle = 'published')")
        with self.assertRaisesRegex(psycopg.errors.RaiseException, "allowed-values"):
            self.apply()


if __name__ == "__main__":
    unittest.main()
