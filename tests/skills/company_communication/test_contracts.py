import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "company-communication"
REFS = SKILL / "references"


class CompanyCommunicationContractsTest(unittest.TestCase):
    def test_required_artifacts_and_eval_cases_exist(self):
        required = [
            "SKILL.md",
            "advanced/advanced.md",
            "examples/success-pattern.md",
            "examples/error-recovery.md",
            "references/api-specs.md",
            "references/changelog.md",
            "references/old-patterns.md",
            "references/eval-suite.json",
            "references/eval-suite.yaml",
            "references/schemas.json",
            "references/skill-pack.json",
            "references/execution-profile.json",
            "scripts/helper_tool.py",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        suite = json.loads((REFS / "eval-suite.json").read_text())
        self.assertEqual(suite["skill_id"], "company-communication")
        self.assertEqual(len(suite["cases"]), 8)

    def test_profile_hashes_bind_to_canonical_artifacts(self):
        suite_bytes = (REFS / "eval-suite.json").read_bytes()
        suite = json.loads(suite_bytes)
        profile = json.loads((REFS / "execution-profile.json").read_text())
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256(suite_bytes).hexdigest())
        self.assertRegex(profile["skill_bundle_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(profile["profile_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(profile["eval_suite_id"], suite["suite_id"])

    def test_schema_is_strict_and_effects_are_empty(self):
        schemas = json.loads((REFS / "schemas.json").read_text())["definitions"]
        self.assertTrue(schemas["input"]["additionalProperties"] is False)
        self.assertTrue(schemas["output"]["additionalProperties"] is False)
        for field in ("messages_sent", "external_calls", "mutations"):
            self.assertEqual(schemas["output"]["properties"]["effects"]["properties"][field]["maxItems"], 0)

    def test_skill_contains_acceptance_boundaries(self):
        text = (SKILL / "SKILL.md").read_text()
        for marker in (
            "plain nontechnical", "Principal", "technical", "agent", "mobile",
            "Other — specify", "uncertainty", "evidence", "complete", "emoji",
            "transport", "untrusted", "credentials",
        ):
            self.assertIn(marker, text, marker)

    def test_helper_is_deterministic_and_has_no_effects(self):
        draft = {
            "status": "READY_FOR_OWNER", "audience": "principal",
            "message": "The verified result is ready.", "evidence": ["test://evidence/1"],
            "effects": {"messages_sent": [], "external_calls": [], "mutations": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            path.write_text(json.dumps(draft))
            command = [sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path), "--mode", "validate"]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})

    def test_helper_rejects_private_data_and_external_effects(self):
        draft = {
            "status": "READY_FOR_OWNER", "audience": "principal",
            "message": "Send customer_email to the vendor.", "evidence": ["test://evidence/1"],
            "effects": {"messages_sent": ["email"], "external_calls": [], "mutations": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            path.write_text(json.dumps(draft))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
