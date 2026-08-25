import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "operational-reporting"
REFS = SKILL / "references"


class OperationalReportingTest(unittest.TestCase):
    def test_required_artifacts_and_modes(self):
        for relative in ("SKILL.md", "advanced/advanced.md", "examples/success-pattern.md", "examples/error-recovery.md", "references/api-specs.md", "references/changelog.md", "references/old-patterns.md", "references/eval-suite.json", "references/eval-suite.yaml", "references/schemas.json", "references/skill-pack.json", "references/execution-profile.json", "scripts/helper_tool.py"):
            self.assertTrue((SKILL / relative).is_file(), relative)
        suite = json.loads((REFS / "eval-suite.json").read_text())
        self.assertEqual(len(suite["cases"]), 9)
        for mode in ("executive_digest", "flash_report", "no_material_change", "supervised_agent_summary", "maintenance_result"):
            self.assertIn(mode, (REFS / "schemas.json").read_text())

    def test_profile_hashes_are_canonical(self):
        from sys import path
        path.insert(0, str(ROOT / "packages" / "core"))
        from linkskills_core.hashing import verify_execution_profile_hashes
        self.assertEqual(verify_execution_profile_hashes(SKILL), [])
        profile = json.loads((REFS / "execution-profile.json").read_text())
        self.assertEqual(profile["eval_suite_hash"], "sha256:" + hashlib.sha256((REFS / "eval-suite.json").read_bytes()).hexdigest())

    def test_strict_schema_and_effect_guards(self):
        definitions = json.loads((REFS / "schemas.json").read_text())["definitions"]
        self.assertFalse(definitions["input"]["additionalProperties"])
        self.assertFalse(definitions["output"]["additionalProperties"])
        for key in ("messages_sent", "external_calls", "mutations"):
            self.assertEqual(definitions["output"]["properties"]["effects"]["properties"][key]["maxItems"], 0)

    def test_acceptance_boundaries_and_migration_are_documented(self):
        text = (SKILL / "SKILL.md").read_text()
        for marker in ("Executive Digest", "Flash Report", "No Material Change", "Supervised-Agent Summary", "Maintenance Result", "morning", "evening", "verified", "Routine", "Principal Tasks", "own mailbox", "Battery Status", "health/selfie", "no emojis", "final checkpoint", "supersedes", "transport"):
            self.assertIn(marker, text, marker)

    def test_helper_no_change_is_deterministic_and_effect_free(self):
        payload = {"mode": "no_material_change", "window": "evening", "records": []}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(payload))
            command = [sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path), "--mode", "render-no-change"]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result["message"], "No material verified change in the supplied window.")
        self.assertEqual(result["effects"], {"messages_sent": [], "external_calls": [], "mutations": []})

    def test_helper_blocks_unverified_completion_and_private_mail(self):
        payload = {"mode": "executive_digest", "window": "morning", "records": [{"kind": "work", "status": "verified_completed", "summary": "done"}, {"kind": "mail", "status": "attention", "summary": "customer_email", "is_own_mailbox": False}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(payload))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        errors = json.loads(result.stdout)["errors"]
        self.assertTrue(any("evidence_pointer" in error for error in errors))
        self.assertTrue(any("mail" in error or "private" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
