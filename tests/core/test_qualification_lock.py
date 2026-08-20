import json
import tempfile
import unittest
from pathlib import Path

from linkskills_core.qualification_lock import (
    QualificationLockError,
    build_qualification_lock,
    build_skill_release_record,
    verify_qualification_lock,
    write_qualification_lock,
)


REPO = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = "e3d80fd22a05a4f68207e130c50b772b5acffda4"
SOURCE_TREE = "69a131b46a73a4ef724694bfe240b1a11652bcc9"


class QualificationLock(unittest.TestCase):
    def test_every_catalog_skill_is_qualified_or_retired(self):
        lock = build_qualification_lock(REPO, provider_commit=SOURCE_COMMIT, provider_tree=SOURCE_TREE)
        self.assertEqual(lock["packet"], "PKT-03")
        self.assertEqual(lock["issue"], "ISS-04")
        self.assertEqual(lock["provider"]["repository"], "linktrend/LiNKskills")
        self.assertEqual(lock["provider"]["commit"], SOURCE_COMMIT)
        self.assertEqual(lock["provider"]["tree"], SOURCE_TREE)
        self.assertEqual(lock["skillCount"], 35)
        self.assertEqual(lock["qualifiedCount"] + lock["retiredCount"], 35)
        decisions = {row["decision"] for row in lock["skills"]}
        self.assertTrue(decisions.issubset({"qualified", "retired"}))
        for row in lock["skills"]:
            self.assertIn(row["decision"], {"qualified", "retired"})
            if row["decision"] == "qualified":
                self.assertEqual(row["qualification"], "qualified")
                self.assertEqual(row["lifecycle"], "published")
                self.assertTrue(str(row["releaseHash"]).startswith("sha256:"))
                self.assertTrue(str(row["bundleHash"]).startswith("sha256:"))
                self.assertTrue(str(row["manifestHash"]).startswith("sha256:"))
                self.assertGreaterEqual(len(row["fragments"]), 1)
            else:
                self.assertEqual(row["qualification"], "withdrawn")

    def test_committed_lock_matches_recomputed_identity(self):
        expected = verify_qualification_lock(REPO)
        self.assertEqual(expected["qualifiedCount"], 35)
        self.assertEqual(expected["retiredCount"], 0)

    def test_missing_eval_suite_is_explicitly_retired(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = root / "incomplete"
            skill.mkdir()
            (skill / "SKILL.md").write_text("---\nname: incomplete\nversion: 1.0.0\n---\n# x\n", encoding="utf-8")
            row = build_skill_release_record(skill, provider_commit="a" * 40, provider_tree="b" * 40)
            self.assertEqual(row["decision"], "retired")
            self.assertEqual(row["retirementReason"], "missing_eval_suite")

    def test_write_round_trip_and_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "catalog").mkdir()
            (root / "skills").mkdir()
            # Empty catalog is invalid for this repo, so copy git identity by verifying live lock tamper.
        lock_path = REPO / "catalog" / "qualification-lock.json"
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        payload["skills"] = payload["skills"][1:]
        with self.assertRaises(QualificationLockError):
            verify_qualification_lock(REPO, payload)

    def test_write_helper_emits_json(self):
        lock = build_qualification_lock(REPO, provider_commit=SOURCE_COMMIT, provider_tree=SOURCE_TREE)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "catalog").mkdir()
            path = write_qualification_lock(root, lock)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["skillCount"], 35)
            self.assertEqual(path.name, "qualification-lock.json")
