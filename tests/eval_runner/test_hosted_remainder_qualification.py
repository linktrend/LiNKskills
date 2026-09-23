"""Hosted remainder qualify: source matrix stays uncertified; publish is separate."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "packages" / "eval_runner"))
sys.path.insert(0, str(REPO / "packages" / "core"))
sys.path.insert(0, str(REPO / "packages" / "gateway"))
sys.path.insert(0, str(REPO / "packages" / "publisher"))
sys.path.insert(0, str(REPO / "packages" / "contracts"))

from linkskills_eval_runner.ed03 import case_records, classify_case_families  # noqa: E402
from linkskills_eval_runner.remainder import (  # noqa: E402
    SHARED_FLOOR_REMAINDER_COUNT,
    UNPUBLISHED_SKILL_IDS,
    qualify_remainder_release_profiles,
    shared_floor_remainder_skill_ids,
)
from linkskills_eval_runner.runner import load_eval_suite  # noqa: E402

MISSING_FROM_59 = (
    "ask-sonner",
    "autoplan",
    "benchmark",
    "canary",
    "cso",
    "design-html",
    "design-sample",
    "devex-review",
    "diagnose-investigate",
    "document-release",
    "gap-design",
    "grill-office-hours",
    "implement",
    "land-and-deploy",
    "mobile-native-web",
    "phase-review",
    "pick-ui-library",
    "plan-ceo-review",
    "plan-eng-review",
    "qa-only",
    "redesign-existing-ui",
    "ship",
    "technical-prd",
    "to-questionnaire",
    "to-tickets",
    "triage",
    "writing-for-agents",
)


def _load_provider_release():
    spec = importlib.util.spec_from_file_location(
        "provider_release", REPO / "scripts" / "provider_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HostedRemainderContractTests(unittest.TestCase):
    def test_source_matrix_never_sets_certified_or_sealed(self) -> None:
        matrix = qualify_remainder_release_profiles(REPO)
        self.assertEqual(matrix["usable"], [])
        self.assertFalse(matrix["usableClaimed"])
        self.assertFalse(matrix["authorizesUsable"])
        for row in matrix["combinations"]:
            self.assertNotEqual(row["lifecycle"], "usable")
            self.assertIn("not_certified", row["reason"])
            self.assertIn("sealed_receipts_unavailable", row["reason"])

    def test_shared_floor_excludes_unpublished_and_initial_five(self) -> None:
        shared = shared_floor_remainder_skill_ids(REPO)
        self.assertEqual(len(shared), SHARED_FLOOR_REMAINDER_COUNT)
        self.assertTrue(UNPUBLISHED_SKILL_IDS.isdisjoint(shared))
        self.assertTrue({"git-safeguard", "tool-architect"}.isdisjoint(shared))

    def test_missing_image_skills_use_helper_tool_execute_blocks(self) -> None:
        for skill_id in MISSING_FROM_59:
            suite = load_eval_suite(REPO / "skills" / skill_id / "references" / "eval-suite.yaml")
            self.assertGreaterEqual(len(suite.cases), 5, skill_id)
            for case in suite.cases:
                execute = case.raw["execute"]
                self.assertEqual(execute["kind"], "consumer_profile", skill_id)
                self.assertEqual(execute["script"], "scripts/helper_tool.py", skill_id)
                self.assertTrue(case.assertions.must_contain, skill_id)
            records = case_records(REPO / "skills" / skill_id)
            families = classify_case_families(records)
            self.assertEqual(
                [name for name in families if not families[name]],
                [],
                skill_id,
            )

    def test_helper_tool_unknown_case_fails_closed(self) -> None:
        helper = REPO / "skills" / "implement" / "scripts" / "helper_tool.py"
        proc = subprocess.run(
            [sys.executable, str(helper), "--case", "not-a-real-case"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "error")
        self.assertFalse(payload["permission_to_act"])
        self.assertFalse(payload["selectable"])

    def test_helper_tool_ordinary_path_is_not_always_pass_stub(self) -> None:
        helper = REPO / "skills" / "ship" / "scripts" / "helper_tool.py"
        proc = subprocess.run(
            [sys.executable, str(helper), "--case", "ship-ordinary-success-path"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["token"], "ship-gate")
        self.assertFalse(payload["permission_to_act"])
        self.assertNotIn("usable", json.dumps(payload))

    def test_five_publish_still_rejects_remainder_ids(self) -> None:
        module = _load_provider_release()
        allowed = module.INITIAL_RELEASE_IDS
        self.assertEqual(len(allowed), 5)
        self.assertNotIn("ship@1.0.0", allowed)
        rows = [{"release_id": f"{sid}@1.0.0"} for sid in shared_floor_remainder_skill_ids(REPO)]
        self.assertEqual(len(rows), 78)
        if len(rows) != 5 or {r["release_id"] for r in rows} != allowed:
            error = "initial_allowlist_mismatch"
        else:
            error = ""
        self.assertEqual(error, "initial_allowlist_mismatch")

    def test_remainder_publish_refuses_unpublished_and_fake_sealed_set(self) -> None:
        module = _load_provider_release()
        os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = "x" * 32
        fake_matrix = {
            "usable": ["personal-compliance@1.0.0/cursor-macos"],
            "combinations": [
                {
                    "id": "personal-compliance@1.0.0/cursor-macos",
                    "skillId": "personal-compliance",
                    "version": "1.0.0",
                    "runtimeProfile": "cursor-macos",
                    "lifecycle": "usable",
                    "run": {
                        "certified": True,
                        "receiptHashes": ["abc"],
                        "networkIsolation": ["denied"],
                    },
                }
            ],
        }
        self.assertEqual(module._sealed_remainder_rows(fake_matrix), [])
        with_ship = {
            "usable": ["ship@1.0.0/cursor-macos"],
            "combinations": [
                {
                    "id": "ship@1.0.0/cursor-macos",
                    "skillId": "ship",
                    "version": "1.0.0",
                    "runtimeProfile": "cursor-macos",
                    "lifecycle": "usable",
                    "run": {
                        "certified": False,
                        "receiptHashes": ["abc"],
                        "networkIsolation": ["denied"],
                    },
                }
            ],
        }
        self.assertEqual(module._sealed_remainder_rows(with_ship), [])


if __name__ == "__main__":
    unittest.main()
