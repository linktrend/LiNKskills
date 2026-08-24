import unittest

from linkskills_librarian.telemetry_v2 import TelemetryPort, validate_report


class TelemetryV2(unittest.TestCase):
    def report(self):
        return {
            "report_kind": "completed_use",
            "score": 9,
            "issue": {"type": "incorrect"},
            "idempotency_key": "a",
            "skill_release_ref": "r",
            "skill_version": "1.0.0",
            "skill_digest": "sha256:" + "a" * 64,
            "consumer_class": "codex",
            "actor_class": "agent_actor",
            "runtime_profile_ref": "p",
            "compatibility": "compatible",
            "outcome": "completed",
            "occurred_at": "2026-08-13T00:00:00Z",
            "received_at": "2026-08-13T00:00:01Z",
            "source_fingerprint": "source:a",
            "privacy": {"raw_content": False, "prohibited_content": False},
            "retention_class": "minimal",
        }

    def test_idempotency_and_privacy(self):
        port = TelemetryPort()
        first = port.submit(self.report())
        self.assertEqual(first, port.submit(self.report()))

        conflict = self.report()
        conflict["score"] = 8
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            port.submit(conflict)

        rejected = self.report()
        rejected["metadata"] = {"nested": [{"prompt": "do not retain"}]}
        result = port.submit(rejected)
        self.assertFalse(result["accepted"])
        self.assertNotIn("prompt", result)
        self.assertEqual(len(port._events), 1)

    def test_required_fields_and_score_union(self):
        for field in (
            "score",
            "skill_release_ref",
            "skill_version",
            "skill_digest",
            "actor_class",
            "runtime_profile_ref",
            "occurred_at",
            "received_at",
            "idempotency_key",
            "source_fingerprint",
            "retention_class",
            "privacy",
        ):
            report = self.report()
            del report[field]
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate_report(report)

        non_use = self.report()
        non_use.update(report_kind="non_use", score=None)
        non_use.pop("issue")
        validate_report(non_use)

    def test_aggregation_is_bounded_to_permitted_dimensions(self):
        port = TelemetryPort()
        port.submit(self.report())
        aggregate = port.aggregate()
        self.assertEqual(
            aggregate,
            {
                ("r", "codex", "agent_actor", "p", "compatible", "incorrect"): 1
            },
        )
        self.assertEqual(len(next(iter(aggregate))), 6)

    def test_private_domain_categories_are_rejected_recursively(self):
        for field in ("calendar", "email", "drive", "battery", "selfie", "image", "identifier", "messages"):
            report = self.report()
            report["metadata"] = {field: "synthetic fixture only"}
            with self.subTest(field=field):
                result = TelemetryPort().submit(report)
                self.assertFalse(result["accepted"])

    def test_feedback_must_be_redacted_and_effects_are_bounded(self):
        report = self.report()
        report["feedback"] = {"redacted": True, "rating": 4}
        report["duration_ms"] = 12
        report["effects"] = ["stdout", "workspace_write"]
        self.assertTrue(TelemetryPort().submit(report)["accepted"])

        unsafe = self.report()
        unsafe["feedback"] = {"redacted": False, "notes": "private transcript"}
        self.assertFalse(TelemetryPort().submit(unsafe)["accepted"])

        effects = self.report()
        effects["effects"] = ["network"]
        self.assertFalse(TelemetryPort().submit(effects)["accepted"])


if __name__ == "__main__":
    unittest.main()
