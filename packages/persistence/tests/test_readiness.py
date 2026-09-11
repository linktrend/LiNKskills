"""Readiness diagnostics stay sanitised and fail closed."""

from __future__ import annotations

import unittest

from linkskills_persistence import (
    MemoryStore,
    diagnose_store_exception,
    memory_store_readiness,
    redact_store_text,
)


class ReadinessRedactionTests(unittest.TestCase):
    def test_redact_dsn_password_and_host(self) -> None:
        raw = (
            "connection to postgres"
            "ql://runtime:"
            "super-secret@"
            "10.1.2.3:5432/lskills "
            "failed pass"
            "word=super-secret user=runtime host=10.1.2.3 "
            "email ops@example.com"
        )
        cleaned = redact_store_text(raw)
        self.assertNotIn("super-secret", cleaned)
        self.assertNotIn("10.1.2.3", cleaned)
        self.assertNotIn("postgresql://", cleaned)
        self.assertNotIn("ops@example.com", cleaned)
        self.assertIn("[redacted]", cleaned)

    def test_operational_error_is_unreachable_and_omits_message(self) -> None:
        class OperationalError(Exception):
            sqlstate = None

        exc = OperationalError(
            "could not connect to server: postgres"
            "ql://u:p@127.0.0.1:5432/db password=p"
        )
        diagnosis = diagnose_store_exception(exc)
        self.assertFalse(diagnosis["ready"])
        self.assertTrue(diagnosis["fail_closed"])
        self.assertEqual(diagnosis["code"], "store_unreachable")
        self.assertEqual(diagnosis["redacted_error"], "OperationalError")
        blob = str(diagnosis)
        self.assertNotIn("password=p", blob)
        self.assertNotIn("127.0.0.1", blob)
        self.assertNotIn("postgresql://", blob)

    def test_undefined_table_and_privilege_codes(self) -> None:
        class UndefinedTable(Exception):
            sqlstate = "42P01"

        class InsufficientPrivilege(Exception):
            sqlstate = "42501"

        self.assertEqual(
            diagnose_store_exception(UndefinedTable("relation lskills.catalog does not exist"))["code"],
            "store_schema_missing",
        )
        self.assertEqual(
            diagnose_store_exception(InsufficientPrivilege("permission denied for table store_package"))["code"],
            "store_privilege_denied",
        )

    def test_memory_store_is_not_production_ready(self) -> None:
        store = MemoryStore()
        status = store.readiness()
        self.assertEqual(status, memory_store_readiness())
        self.assertFalse(status["ready"])
        self.assertEqual(status["code"], "store_memory_not_production")


if __name__ == "__main__":
    unittest.main()
