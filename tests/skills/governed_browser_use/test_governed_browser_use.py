"""Focused contract and fail-closed tests for PKT-07."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills/governed-browser-use"
HELPER_PATH = SKILL / "scripts/helper_tool.py"
sys.path.insert(0, str(ROOT / "packages/contracts"))
from linkskills_contracts import validate_instance  # noqa: E402


def load_helper():
    """Load the offline helper without installing the skill as a package."""

    spec = importlib.util.spec_from_file_location("governed_browser_helper", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()


def request(action: str, **overrides):
    """Return a valid baseline request with explicit safe defaults."""

    value = {
        "task_id": "20260824-0001-ABC123-000001",
        "target": "https://public.example.test",
        "requested_action": action,
        "content_trust": "static_or_api",
        "brain_rules": ["advisory: require owner review for external effects"],
        "approval": "none",
        "credentials_present": False,
        "private_network": False,
        "bot_protection": "none",
        "download_requested": False,
        "standing_rule": "none",
    }
    value.update(overrides)
    return value


class GovernedBrowserUseTests(unittest.TestCase):
    """Verify classification, effects, schema binding, and safety boundaries."""

    def setUp(self):
        self.schemas = json.loads((SKILL / "references/schemas.json").read_text())[
            "definitions"
        ]

    def assert_valid_output(self, output):
        """Require every helper result to satisfy the output contract."""

        checked = validate_instance(output, self.schemas["output"])
        self.assertTrue(checked.ok, checked.errors)
        self.assertEqual(output["effects"], {
            "external_calls": [],
            "mutations": [],
            "messages_sent": [],
            "downloads_opened": [],
        })
        self.assertTrue(output["rollback"].startswith("ABSENT@"))

    def test_public_read_is_effect_free(self):
        output = HELPER.classify(request("public_read"))
        self.assertEqual(output["status"], "COMPLETED")
        self.assertEqual(output["approval"]["status"], "NOT_REQUIRED")
        self.assert_valid_output(output)

    def test_prepare_form_never_submits(self):
        output = HELPER.classify(request("prepare_form"))
        self.assertEqual(output["status"], "COMPLETED")
        self.assertIn("no-submit", output["controls"])
        self.assert_valid_output(output)

    def test_authenticated_read_stops_for_approval(self):
        output = HELPER.classify(request("authenticated_read"))
        self.assertEqual(output["status"], "PENDING_APPROVAL")
        self.assertEqual(output["approval"]["status"], "PENDING_APPROVAL")
        self.assert_valid_output(output)

    def test_reversible_change_stops_for_approval(self):
        output = HELPER.classify(request("reversible_change"))
        self.assertEqual(output["status"], "PENDING_APPROVAL")
        self.assert_valid_output(output)

    def test_communication_is_draft_only(self):
        output = HELPER.classify(request("communication"))
        self.assertEqual(output["status"], "PENDING_APPROVAL")
        self.assertEqual(output["effects"]["messages_sent"], [])
        self.assert_valid_output(output)

    def test_commitment_and_purchase_are_denied(self):
        for action in ("commitment", "purchase_legal"):
            with self.subTest(action=action):
                output = HELPER.classify(request(action))
                self.assertEqual(output["status"], "DENIED")
                self.assert_valid_output(output)

    def test_upload_download_requires_destination_review(self):
        output = HELPER.classify(request("upload_download", download_requested=True))
        self.assertEqual(output["status"], "PENDING_APPROVAL")
        self.assertIn("no-auto-open-download", output["controls"])
        self.assert_valid_output(output)

    def test_credentials_and_private_network_fail_closed(self):
        for overrides in (
            {"credentials_present": True},
            {"private_network": True},
        ):
            with self.subTest(overrides=overrides):
                output = HELPER.classify(request("public_read", **overrides))
                self.assertEqual(output["status"], "DENIED")
                self.assertEqual(output["action_class"], "prohibited")
                self.assert_valid_output(output)

    def test_untrusted_content_and_bot_uncertainty_stop(self):
        for overrides in (
            {"content_trust": "untrusted_page"},
            {"bot_protection": "uncertain"},
        ):
            with self.subTest(overrides=overrides):
                output = HELPER.classify(request("public_read", **overrides))
                self.assertEqual(output["status"], "PENDING_APPROVAL")
                self.assert_valid_output(output)

    def test_standing_rule_activation_and_unknown_action_fail_closed(self):
        activated = HELPER.classify(request("public_read", standing_rule="activate"))
        self.assertEqual(activated["status"], "DENIED")
        unknown = HELPER.classify(request("not_declared"))
        self.assertEqual(unknown["status"], "DENIED")
        self.assertEqual(unknown["action_class"], "prohibited")
        self.assert_valid_output(activated)
        self.assert_valid_output(unknown)

    def test_input_schema_rejects_undeclared_action(self):
        checked = validate_instance(request("not_declared"), self.schemas["input"])
        self.assertFalse(checked.ok)

    def test_helper_is_offline_and_contract_has_required_sections(self):
        source = HELPER_PATH.read_text()
        for forbidden in ("requests", "urllib", "subprocess", "socket"):
            self.assertNotIn(forbidden, source)
        skill_text = (SKILL / "SKILL.md").read_text()
        for required in ("Decision tree", "Action-class matrix", "Untrusted web content", "Contracts and evidence", "Scope and ownership"):
            self.assertIn(required, skill_text)


if __name__ == "__main__":
    unittest.main()
