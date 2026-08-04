"""Tests for classification-ledger certification overlay + batch certifier gates."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)

# Promoting overlay checks reject the repository-visible local key. Unit tests
# that assert usable promotion mint + verify under this process-only test key.
PROMOTING_TEST_ISSUER_KEY = "linkskills-promoting-unit-test-issuer-key-not-for-ci-secret"

from lib.skill_runtime.catalog import build_catalog_index
from lib.skill_runtime.certification_overlay import (
    load_certification_overlay,
    overlay_from_ledger,
    resolve_repo_contained_path,
    verify_sealed_live_evidence,
)


def _seal_receipt(**overrides: Any) -> Dict[str, Any]:
    """Build a sealed executor receipt matching core/eval seal contract."""
    signing_key = overrides.pop("_signing_key", None)
    base: Dict[str, Any] = {
        "receipt_id": "rcpt-1",
        "case_id": "c1",
        "skill_id": "demo-skill",
        "suite_id": "suite-1",
        "suite_hash": "suitehash-aaa",
        "skill_release_hash": "skill-release:abc123",
        "execution_profile_hash": "profilehash-bbb",
        "environment": {"python_version": "3.11"},
        "toolchain": {"tools": [{"tool_id": "text-echo", "version": "1.0.0"}]},
        "tool_calls": [
            {
                "tool_id": "text-echo",
                "version": "1.0.0",
                "tool_hash": "toolhash-ccc",
                "exit_code": 0,
            }
        ],
        "exit_code": 0,
        "stdout_hash": "stdout",
        "stderr_hash": "stderr",
        "artifact_hashes": [],
        "started_at": "2026-08-03T00:00:00Z",
        "finished_at": "2026-08-03T00:00:01Z",
        "executor_version": "linkskills-eval-executor/0.4.0",
        "evidence_source": "executor",
        "network_isolation": "denied",
        "provenance_kind": "eval_runner_hmac_v1",
        "issuer_id": "linkskills-eval-runner-test",
    }
    base.update(overrides)
    payload = {
        "artifact_hashes": list(base.get("artifact_hashes") or []),
        "case_id": base["case_id"],
        "environment": dict(base.get("environment") or {}),
        "evidence_source": base["evidence_source"],
        "execution_profile_hash": base["execution_profile_hash"],
        "executor_version": base["executor_version"],
        "exit_code": base.get("exit_code"),
        "finished_at": base["finished_at"],
        "issuer_id": base["issuer_id"],
        "network_isolation": base["network_isolation"],
        "provenance_kind": base["provenance_kind"],
        "receipt_id": base["receipt_id"],
        "skill_id": base["skill_id"],
        "skill_release_hash": base["skill_release_hash"],
        "started_at": base["started_at"],
        "stderr_hash": base["stderr_hash"],
        "stdout_hash": base["stdout_hash"],
        "suite_hash": base["suite_hash"],
        "suite_id": base["suite_id"],
        "tool_calls": list(base.get("tool_calls") or []),
        "toolchain": dict(base.get("toolchain") or {}),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()
    base["receipt_hash"] = digest
    if signing_key is not None:
        key = str(signing_key).encode("utf-8")
    else:
        key = os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"].encode("utf-8")
    base["issuer_signature"] = hmac.new(key, digest.encode("utf-8"), hashlib.sha256).hexdigest()
    return base


def _with_promoting_key() -> None:
    os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = PROMOTING_TEST_ISSUER_KEY


def _seal_promoting_receipt(**overrides: Any) -> Dict[str, Any]:
    return _seal_receipt(_signing_key=PROMOTING_TEST_ISSUER_KEY, **overrides)


def _write_sealed_evidence(
    root: Path,
    rel: str,
    *,
    skill_id: str = "demo-skill",
    receipt: Optional[Dict[str, Any]] = None,
    certified: bool = True,
    case_status: str = "passed",
    extra_top: Optional[Dict[str, Any]] = None,
) -> str:
    """Write a minimal sealed evidence JSON under ``root``; return relative path."""
    rcpt = receipt if receipt is not None else _seal_receipt(skill_id=skill_id)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    doc: Dict[str, Any] = {
        "skill_id": skill_id,
        "skill_release_hash": rcpt["skill_release_hash"],
        "suite_hash": rcpt["suite_hash"],
        "profile_hash": rcpt["execution_profile_hash"],
        "certified": certified,
        "cases": [
            {
                "case_id": rcpt["case_id"],
                "evidence_source": "executor",
                "status": case_status,
                "execution_receipt": rcpt,
            }
        ],
        "execution_receipts": [rcpt],
    }
    if extra_top:
        doc.update(extra_top)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return rel


class CertificationOverlayTests(unittest.TestCase):
    def test_usable_without_sealed_evidence_falls_back_to_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "canary-echo": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [],
                        },
                        "git-safeguard": {
                            "classification": "draft",
                            "sealed_live_receipt_evidence": [],
                        },
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["canary-echo"], "draft")
            self.assertEqual(overlay["git-safeguard"], "draft")

    def test_usable_nonexistent_path_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [
                                "evidence/phase10/sealed/missing.json"
                            ],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_malformed_json_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "evidence" / "phase10" / "sealed" / "bad.json"
            bad.parent.mkdir(parents=True)
            bad.write_text("{not-json", encoding="utf-8")
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [
                                "evidence/phase10/sealed/bad.json"
                            ],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_malformed_receipt_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "evidence/phase10/sealed/incomplete.json"
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "certified": True,
                        "cases": [
                            {
                                "case_id": "c1",
                                "status": "passed",
                                "evidence_source": "executor",
                                "execution_receipt": {"skill_id": "demo-skill"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_tampered_hmac_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = _seal_receipt(skill_id="demo-skill")
            receipt["issuer_signature"] = "0" * 64
            rel = _write_sealed_evidence(root, "evidence/phase10/sealed/tampered.json", receipt=receipt)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                            "skill_release_hash": receipt["skill_release_hash"],
                            "profile_hash": receipt["execution_profile_hash"],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_cross_skill_receipt_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = _seal_receipt(skill_id="other-skill")
            rel = _write_sealed_evidence(
                root,
                "evidence/phase10/sealed/cross.json",
                skill_id="other-skill",
                receipt=receipt,
            )
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                            "skill_release_hash": receipt["skill_release_hash"],
                            "profile_hash": receipt["execution_profile_hash"],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_release_hash_drift_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = _seal_receipt(skill_id="demo-skill")
            rel = _write_sealed_evidence(root, "evidence/phase10/sealed/ok.json", receipt=receipt)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                            "skill_release_hash": "skill-release:WRONG",
                            "profile_hash": receipt["execution_profile_hash"],
                            "suite_hash": receipt["suite_hash"],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_profile_hash_drift_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = _seal_receipt(skill_id="demo-skill")
            rel = _write_sealed_evidence(root, "evidence/phase10/sealed/ok.json", receipt=receipt)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                            "skill_release_hash": receipt["skill_release_hash"],
                            "profile_hash": "profile-WRONG",
                            "suite_hash": receipt["suite_hash"],
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_suite_hash_drift_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = _seal_receipt(skill_id="demo-skill")
            rel = _write_sealed_evidence(root, "evidence/phase10/sealed/ok.json", receipt=receipt)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                            "skill_release_hash": receipt["skill_release_hash"],
                            "profile_hash": receipt["execution_profile_hash"],
                            "suite_hash": "suite-WRONG",
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_tool_hash_drift_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = _seal_receipt(skill_id="demo-skill")
            rel = _write_sealed_evidence(root, "evidence/phase10/sealed/ok.json", receipt=receipt)
            overlay = overlay_from_ledger(
                {
                    "skills": {
                        "demo-skill": {
                            "classification": "usable",
                            "sealed_live_receipt_evidence": [rel],
                            "skill_release_hash": receipt["skill_release_hash"],
                            "profile_hash": receipt["execution_profile_hash"],
                            "suite_hash": receipt["suite_hash"],
                            "tool_hash": "tool-WRONG",
                        }
                    }
                },
                repo_root=root,
            )
            self.assertEqual(overlay["demo-skill"], "draft")

    def test_usable_path_escape_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = Path(tmp).parent / "outside-sealed.json"
            try:
                outside.write_text("{}", encoding="utf-8")
                overlay = overlay_from_ledger(
                    {
                        "skills": {
                            "demo-skill": {
                                "classification": "usable",
                                "sealed_live_receipt_evidence": [str(outside)],
                            }
                        }
                    },
                    repo_root=root,
                )
                self.assertEqual(overlay["demo-skill"], "draft")
                self.assertIsNone(resolve_repo_contained_path(root, "../outside-sealed.json"))
            finally:
                if outside.exists():
                    outside.unlink()

    def test_usable_with_valid_sealed_receipt_promotes(self) -> None:
        prior = os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY")
        _with_promoting_key()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                receipt = _seal_promoting_receipt(skill_id="demo-skill")
                rel = _write_sealed_evidence(
                    root, "evidence/phase10/sealed/demo.json", receipt=receipt
                )
                overlay = overlay_from_ledger(
                    {
                        "skills": {
                            "demo-skill": {
                                "classification": "usable",
                                "sealed_live_receipt_evidence": [rel],
                                "skill_release_hash": receipt["skill_release_hash"],
                                "profile_hash": receipt["execution_profile_hash"],
                                "suite_hash": receipt["suite_hash"],
                                "tool_hash": "toolhash-ccc",
                            }
                        }
                    },
                    repo_root=root,
                )
                self.assertEqual(overlay["demo-skill"], "usable")
        finally:
            if prior is None:
                os.environ.pop("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", None)
            else:
                os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = prior

    def test_build_catalog_applies_overlay_with_valid_receipt(self) -> None:
        prior = os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY")
        _with_promoting_key()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                skill = root / "skills" / "demo-skill"
                (skill / "references").mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    "---\nname: demo-skill\ndescription: d\nversion: 0.1.0\n"
                    "usage_trigger: t\nformat_profile: simple\n---\n# demo\n",
                    encoding="utf-8",
                )
                (skill / "references" / "eval-suite.yaml").write_text(
                    "skill_id: demo-skill\n", encoding="utf-8"
                )
                receipt = _seal_promoting_receipt(skill_id="demo-skill")
                rel = _write_sealed_evidence(
                    root, "evidence/phase10/sealed/demo.json", receipt=receipt
                )
                ledger_dir = root / "evidence" / "phase10"
                ledger_dir.mkdir(parents=True, exist_ok=True)
                (ledger_dir / "skill-classification-draft.json").write_text(
                    json.dumps(
                        {
                            "skills": {
                                "demo-skill": {
                                    "classification": "usable",
                                    "sealed_live_receipt_evidence": [rel],
                                    "skill_release_hash": receipt["skill_release_hash"],
                                    "profile_hash": receipt["execution_profile_hash"],
                                }
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                overlay = load_certification_overlay(root)
                index = build_catalog_index(root, certification_overlay=overlay)
                self.assertEqual(index["skill_count"], 1)
                self.assertEqual(index["skills"][0]["certification_state"], "usable")
        finally:
            if prior is None:
                os.environ.pop("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", None)
            else:
                os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = prior

    def test_build_catalog_nonexistent_evidence_stays_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "demo-skill"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: d\nversion: 0.1.0\n"
                "usage_trigger: t\nformat_profile: simple\n---\n# demo\n",
                encoding="utf-8",
            )
            (skill / "references" / "eval-suite.yaml").write_text(
                "skill_id: demo-skill\n", encoding="utf-8"
            )
            ledger_dir = root / "evidence" / "phase10"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "skill-classification-draft.json").write_text(
                json.dumps(
                    {
                        "skills": {
                            "demo-skill": {
                                "classification": "usable",
                                "sealed_live_receipt_evidence": [
                                    "evidence/phase10/sealed/demo.json"
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            overlay = load_certification_overlay(root)
            index = build_catalog_index(root, certification_overlay=overlay)
            self.assertEqual(index["skills"][0]["certification_state"], "draft")


class CatalogCanarySkillTests(unittest.TestCase):
    def test_canary_echo_exists_with_executable_suite(self) -> None:
        skill = REPO_ROOT / "skills" / "canary-echo"
        suite = skill / "references" / "eval-suite.yaml"
        self.assertTrue(skill.is_dir())
        self.assertTrue(suite.is_file())
        text = suite.read_text(encoding="utf-8")
        self.assertIn("packaged_tool", text)
        self.assertIn("text-echo", text)
        self.assertIn("scenarios:", text)

    def test_repo_overlay_loader_requires_promoting_issuer_for_canary(self) -> None:
        """Public/local-dev key must not promote canary; promoting key may.

        Without an externally supplied promoting issuer key, overlay fail-closes
        to draft even when sealed evidence paths are present.
        """
        prior = os.environ.get("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY")
        try:
            os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = (
                "linkskills-local-eval-runner-issuer-key-not-for-production"
            )
            overlay = load_certification_overlay(REPO_ROOT)
            self.assertNotEqual(
                overlay.get("canary-echo"),
                "usable",
                msg="local-dev issuer key must never authorize usable promotion",
            )

            promoting = os.environ.get("LINKSKILLS_PROMOTING_OVERLAY_TEST_KEY", "").strip()
            if not promoting:
                self.skipTest(
                    "set LINKSKILLS_PROMOTING_OVERLAY_TEST_KEY to the process-only "
                    "key that signed evidence/phase10/sealed/canary-echo-sealed.json"
                )
            os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = promoting
            overlay = load_certification_overlay(REPO_ROOT)
            self.assertEqual(overlay.get("canary-echo"), "usable")
            ledger = json.loads(
                (REPO_ROOT / "evidence/phase10/skill-classification-draft.json").read_text(
                    encoding="utf-8"
                )
            )
            entry = ledger["skills"]["canary-echo"]
            self.assertTrue(verify_sealed_live_evidence(REPO_ROOT, "canary-echo", entry))
        finally:
            if prior is None:
                os.environ.pop("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", None)
            else:
                os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = prior


if __name__ == "__main__":
    unittest.main()
