"""Negative tests for scripts/certify-catalog.py exit policy + toolchain binding."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages" / "tool_runtime"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "eval_runner"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "contracts"))


def _load_certify_catalog():
    path = REPO_ROOT / "scripts" / "certify-catalog.py"
    spec = importlib.util.spec_from_file_location("certify_catalog_under_test", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CERTIFY = _load_certify_catalog()


def _write_executable_skill(root: Path, skill_id: str = "canary-echo") -> Path:
    skill = root / "skills" / skill_id
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {skill_id}\ndescription: fixture\nversion: 0.1.0\n"
        "usage_trigger: t\nformat_profile: simple\n---\n# fixture\n",
        encoding="utf-8",
    )
    (skill / "references" / "eval-suite.yaml").write_text(
        f"""
schema_version: "0.1"
suite_id: {skill_id}-suite
skill_id: {skill_id}
suite_version: 0.1.0
pass_threshold: 0.8
rubric:
  - dimension: correctness
    weight: 1.0
scenarios:
  - id: echo
    execute:
      kind: packaged_tool
      tool_id: text-echo
      tool_dir: tools/text-echo
      version: "1.0.0"
      argv: ["PING"]
    assertions:
      must_contain: ["PING"]
      exit_code: 0
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return skill


class CertificationExitCodeTests(unittest.TestCase):
    def test_full_catalog_sealed_zero_usable_exits_nonzero(self) -> None:
        code = CERTIFY.certification_exit_code(
            {"usable_count": 0, "results": [{"skill_id": "a", "classification": "draft"}]},
            requested_skills=[],
            require_sealed=True,
        )
        self.assertEqual(code, 1)

    def test_full_catalog_sealed_with_usable_ok(self) -> None:
        code = CERTIFY.certification_exit_code(
            {
                "usable_count": 1,
                "results": [
                    {"skill_id": "canary-echo", "classification": "usable"},
                    {"skill_id": "other", "classification": "draft"},
                ],
            },
            requested_skills=[],
            require_sealed=True,
        )
        self.assertEqual(code, 0)

    def test_requested_skill_sealed_failure_exits_nonzero(self) -> None:
        code = CERTIFY.certification_exit_code(
            {
                "usable_count": 0,
                "results": [{"skill_id": "canary-echo", "classification": "draft"}],
            },
            requested_skills=["canary-echo"],
            require_sealed=True,
        )
        self.assertEqual(code, 1)

    def test_unsealed_always_zero(self) -> None:
        code = CERTIFY.certification_exit_code(
            {"usable_count": 0, "results": []},
            requested_skills=["canary-echo"],
            require_sealed=False,
        )
        self.assertEqual(code, 0)


class CanaryToolchainHashTests(unittest.TestCase):
    def test_build_canary_toolchain_binds_source_and_tool_hash(self) -> None:
        toolchain = CERTIFY.build_canary_toolchain(REPO_ROOT)
        tools = toolchain["tools"]
        self.assertEqual(len(tools), 1)
        entry = tools[0]
        self.assertEqual(entry["tool_id"], "text-echo")
        self.assertEqual(entry["version"], "1.0.0")
        self.assertTrue(entry["source_hash"])
        self.assertEqual(entry["tool_hash"], entry["source_hash"])
        # Drift of tool code must change profile identity via toolchain mapping.
        from linkskills_eval_runner.executor import (
            compute_execution_profile_hash,
            compute_skill_release_hash,
        )
        from linkskills_eval_runner.runner import load_eval_suite

        suite = load_eval_suite(REPO_ROOT / "skills" / "canary-echo" / "references" / "eval-suite.yaml")
        release = compute_skill_release_hash(REPO_ROOT / "skills" / "canary-echo")
        h_bound = compute_execution_profile_hash(
            suite=suite, toolchain=toolchain, skill_release_hash=release
        )
        h_unbound = compute_execution_profile_hash(
            suite=suite,
            toolchain={"tools": [{"tool_id": "text-echo", "version": "1.0.0"}]},
            skill_release_hash=release,
        )
        self.assertNotEqual(h_bound, h_unbound)
        drifted = {
            "tools": [
                {
                    **entry,
                    "source_hash": "0" * 64,
                    "tool_hash": "0" * 64,
                }
            ]
        }
        h_drift = compute_execution_profile_hash(
            suite=suite, toolchain=drifted, skill_release_hash=release
        )
        self.assertNotEqual(h_bound, h_drift)


class CertifyCatalogSealedFailureExitTests(unittest.TestCase):
    def test_sealed_cert_failure_exits_nonzero_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="certify-exit-") as tmp:
            root = Path(tmp)
            _write_executable_skill(root, "canary-echo")
            # Provide tools/text-echo so toolchain resolve succeeds when reached.
            import shutil

            shutil.copytree(REPO_ROOT / "tools" / "text-echo", root / "tools" / "text-echo")

            with mock.patch.object(CERTIFY, "_proven_isolation_available", return_value=False):
                code = CERTIFY.main(
                    [
                        "--repo-root",
                        str(root),
                        "--skill",
                        "canary-echo",
                        "--no-write-ledger",
                        "--no-rebuild-catalog",
                    ]
                )

            self.assertEqual(code, 1)
            report_path = root / CERTIFY.REPORT_REL
            self.assertTrue(report_path.is_file(), msg="report must be written before nonzero exit")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["require_sealed"])
            self.assertEqual(report["usable_count"], 0)
            self.assertEqual(report["results"][0]["reason_code"], "isolation_unavailable")
            self.assertEqual(report["results"][0]["classification"], "draft")


if __name__ == "__main__":
    unittest.main()
