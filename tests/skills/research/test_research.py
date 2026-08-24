"""PKT-06 contract, boundary, migration, and privacy regressions."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "skills" / "research"
sys.path.insert(0, str(ROOT / "packages" / "contracts"))
sys.path.insert(0, str(ROOT / "packages" / "core"))

from linkskills_contracts import validate_instance  # noqa: E402
from linkskills_core.hashing import verify_execution_profile_hashes  # noqa: E402


class ResearchSkillTests(unittest.TestCase):
    def test_manifest_contains_complete_canonical_research_pack(self) -> None:
        required = (
            "SKILL.md",
            "advanced/advanced.md",
            "examples/success-pattern.md",
            "examples/error-recovery.md",
            "references/api-specs.md",
            "references/changelog.md",
            "references/eval-suite.json",
            "references/eval-suite.yaml",
            "references/execution-profile.json",
            "references/old-patterns.md",
            "references/overlap-migration.md",
            "references/schemas.json",
            "references/skill-pack.json",
            "scripts/helper_tool.py",
        )
        for rel in required:
            self.assertTrue((RESEARCH / rel).is_file(), rel)

    def test_canonical_artifacts_and_profile_hashes(self) -> None:
        for rel, schema_name in (("skill-pack.json", "skill-pack"), ("execution-profile.json", "execution-profile")):
            payload = json.loads((RESEARCH / "references" / rel).read_text(encoding="utf-8"))
            self.assertTrue(validate_instance(payload, schema_name).ok)
        self.assertEqual(verify_execution_profile_hashes(RESEARCH), [])

    def test_input_output_contracts_are_strict_and_effect_free(self) -> None:
        schemas = json.loads((RESEARCH / "references" / "schemas.json").read_text(encoding="utf-8"))["definitions"]
        valid_input = {
            "question": "Which official API limit is current?",
            "decision": "Choose the compatible integration path",
            "confidence_threshold": 0.8,
            "freshness_required": True,
            "max_cost_tier": "web",
            "privacy_classification": "public",
        }
        self.assertTrue(validate_instance(valid_input, schemas["input"]).ok)
        invalid_input = dict(valid_input, unexpected="reject")
        self.assertFalse(validate_instance(invalid_input, schemas["input"]).ok)
        valid_output = {
            "status": "COMPLETED",
            "report": "Observed fact with a cited primary source.",
            "claims": [{"claim_id": "c1", "claim_text": "A fact", "evidence_class": "observed_fact", "source_pointers": ["https://example.com"], "confidence": 0.9}],
            "sources": [{"source_type": "primary", "pointer": "https://example.com", "retrieved_at": "2026-08-24T00:00:00Z"}],
            "uncertainties": [],
            "effects": {"external_calls": [], "mutations": []},
        }
        self.assertTrue(validate_instance(valid_output, schemas["output"]).ok)
        invalid_output = dict(valid_output, effects={"external_calls": ["network"], "mutations": []})
        self.assertFalse(validate_instance(invalid_output, schemas["output"]).ok)

    def test_acceptance_controls_are_present(self) -> None:
        text = (RESEARCH / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in ("observed fact", "inference", "assumption", "hypothesis", "recommendation", "currentness", "primary", "conflict", "untrusted data", "prompt", "private", "citation-enforcer", "pending_approval", "proceed", "native cli", "cli wrapper", "direct api", "mcp"):
            self.assertIn(marker, text)

    def test_eval_covers_required_adversarial_classes(self) -> None:
        suite = json.loads((RESEARCH / "references" / "eval-suite.json").read_text(encoding="utf-8"))
        case_ids = {case["case_id"] for case in suite["cases"]}
        for required in ("primary-current-source-brief", "conflicting-dated-sources", "prompt-injection-in-retrieved-content", "private-data-request", "deep-brief-approval-gate", "citation-enforcer-circular-summary", "stable-supplied-evidence-no-search", "legacy-search-strategy-migration"):
            self.assertIn(required, case_ids)

    def test_explicit_overlap_migration_keeps_legacy_releases_immutable(self) -> None:
        migration = (RESEARCH / "references/overlap-migration.md").read_text(encoding="utf-8").lower()
        self.assertIn("search-strategy", migration)
        self.assertIn("immutable", migration)
        self.assertIn("supersed", migration)
        self.assertIn("citation-enforcer", migration)
        self.assertIn("tools/research", migration)

    def test_local_helper_is_deterministic_and_has_no_effects(self) -> None:
        payload = {"claims": [{"claim_id": "c1", "claim_text": "A"}], "sources": [{"source_type": "file", "pointer": "brief.md"}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(RESEARCH / "scripts/helper_tool.py"), "--input", str(path)], capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "SUCCESS")
        self.assertEqual(output["external_calls"], [])
        self.assertEqual(output["mutations"], [])

    def test_private_or_injection_content_is_explicitly_out_of_scope(self) -> None:
        skill = (RESEARCH / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("credentials", skill)
        self.assertIn("prompt injection", skill)
        self.assertIn("raw sensitive", skill)
        self.assertIn("do not follow", (RESEARCH / "advanced/advanced.md").read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
