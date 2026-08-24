from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "executive-decisions-governance"


def load_helper():
    spec = importlib.util.spec_from_file_location("executive_decisions_helper", SKILL / "scripts" / "helper_tool.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExecutiveDecisionsGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(ROOT / "packages" / "contracts"))
        from linkskills_contracts import validate_instance
        cls.validate_instance = staticmethod(validate_instance)
        cls.schemas = json.loads((SKILL / "references" / "schemas.json").read_text(encoding="utf-8"))["definitions"]

    def evidence(self, status="confirmed"):
        return [{"ref": "fixture:decision-pkt13-001", "status": status}]

    def request(self, mode="decision_brief", **extra):
        request = {
            "mode": mode,
            "privacy_classification": "synthetic",
            "matter_ref": "matter:pricing-review-001",
            "matter": "Review a synthetic pricing change.",
            "source_evidence": self.evidence(),
            "risks": ["Demand response is uncertain."],
            "choices": [
                {"id": "retain", "label": "Retain current pricing", "tradeoff": "Lower change risk; slower learning."},
                {"id": "test", "label": "Run a limited test", "tradeoff": "Faster learning; requires owner review."},
                {"id": "other", "label": "Other — specify", "tradeoff": "Owner may name another bounded option."},
            ],
            "recommendation": "Run a limited test, subject to owner review.",
        }
        request.update(extra)
        return request

    def assert_valid_output(self, output):
        output_schema = dict(self.schemas["output"])
        output_schema["definitions"] = self.schemas
        result = self.validate_instance(output, output_schema)
        self.assertTrue(result.ok, msg=[str(error) for error in result.errors])

    def test_required_artifacts_and_scope_surface(self):
        required = [
            "SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md",
            "references/api-specs.md", "references/changelog.md", "references/eval-suite.json",
            "references/eval-suite.yaml", "references/old-patterns.md", "references/schemas.json",
            "references/skill-pack.json", "scripts/README.md", "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        content = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in ("matter", "evidence", "risks", "choices", "recommendation", "other — specify", "rule impact", "implementation", "authority", "mobile", "not_reported"):
            self.assertIn(marker, content)
        self.assertNotIn("approve, activate, or enforce", content.split("## authority", 1)[-1].split("## tooling", 1)[0])

    def test_valid_brief_is_owner_ready_with_empty_effects(self):
        result = load_helper().normalize_request(self.request())
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assert_valid_output(result)
        self.assertEqual(result["matter_ref"], "matter:pricing-review-001")
        self.assertEqual(result["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})
        self.assertFalse(result["authority"]["activated"])

    def test_missing_evidence_and_ambiguous_source_stay_honest(self):
        helper = load_helper()
        missing = helper.normalize_request(self.request(source_evidence=[]))
        self.assertEqual(missing["status"], "BLOCKED")
        self.assert_valid_output(missing)
        uncertain = helper.normalize_request(self.request(source_evidence=self.evidence("not_reported")))
        self.assertEqual(uncertain["status"], "DRAFT")
        self.assertTrue(uncertain["uncertainty"])
        self.assert_valid_output(uncertain)

    def test_approved_decision_rule_impact_and_tracking_never_activate(self):
        request = self.request(
            mode="record_decision",
            decision_record={"status": "approved", "choice_id": "test", "owner_ref": "owner:principal", "recorded_at": "2026-08-24"},
            rule_impact={"status": "approved", "summary": "Owner-supplied impact record only.", "scope": "Synthetic pricing test", "owner_ref": "owner:principal"},
            implementation_tracking=[{"id": "track-001", "item": "Prepare owner review note", "owner_ref": "owner:principal", "status": "proposed", "evidence_ref": "fixture:decision-pkt13-001"}],
        )
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "READY_FOR_OWNER")
        self.assertFalse(result["authority"]["approval_recorded"])
        self.assertFalse(result["authority"]["activated"])
        self.assert_valid_output(result)

    def test_invalid_tracking_status_fails_closed_without_echoing_invalid_item(self):
        request = self.request(
            mode="implementation_tracking",
            implementation_tracking=[{"id": "track-001", "item": "Prepare owner review note", "owner_ref": "owner:principal", "status": "approved", "evidence_ref": "fixture:decision-pkt13-001"}],
        )
        result = load_helper().normalize_request(request)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["implementation_tracking"], [])
        self.assert_valid_output(result)

    def test_authority_privacy_and_duplicate_boundaries_fail_closed(self):
        helper = load_helper()
        for action in ("activate", "enforce", "send", "schedule", "create_task"):
            result = helper.normalize_request(self.request(requested_action=action))
            self.assertEqual(result["status"], "BLOCKED", action)
            self.assert_valid_output(result)
        private = helper.normalize_request(self.request(matter="customer@example.com"))
        self.assertEqual(private["status"], "BLOCKED")
        self.assert_valid_output(private)
        duplicate = self.request()
        duplicate["source_evidence"] = self.evidence() + [{"ref": "fixture:decision-pkt13-001", "status": "confirmed"}]
        repeated = helper.normalize_request(duplicate)
        self.assertEqual(repeated["status"], "BLOCKED")
        self.assert_valid_output(repeated)


if __name__ == "__main__":
    unittest.main()
