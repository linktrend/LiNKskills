"""Negative tests for sealed-cert release vs local non-promoting modes.

Proves missing key, repository-visible dev key, floating image, and local
non-promoting mode cannot authorize promoting usable artifacts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "eval_runner"))

from lib.skill_runtime.sealed_cert_mode import (  # noqa: E402
    LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
    MODE_LOCAL_NON_PROMOTING,
    MODE_RELEASE,
    is_digest_pinned_image,
    is_local_dev_issuer_key,
    non_promoting_classification,
    promoting_issuer_keys,
    validate_sealed_cert_preflight,
)


class SealedCertModeUnitTests(unittest.TestCase):
    def test_local_dev_key_detected(self) -> None:
        self.assertTrue(is_local_dev_issuer_key(LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY))
        self.assertFalse(is_local_dev_issuer_key("ephemeral-process-only-key"))
        self.assertFalse(is_local_dev_issuer_key(""))

    def test_digest_pin_required_shape(self) -> None:
        self.assertTrue(
            is_digest_pinned_image(
                "python@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            )
        )
        self.assertFalse(is_digest_pinned_image("python:3.12-slim"))
        self.assertFalse(is_digest_pinned_image("python:3.12-slim@sha256:dead"))
        self.assertFalse(is_digest_pinned_image(""))

    def test_release_mode_missing_key_fails_closed(self) -> None:
        result = validate_sealed_cert_preflight(
            mode=MODE_RELEASE,
            issuer_key="",
            image=(
                "python@sha256:0123456789abcdef0123456789abcdef"
                "0123456789abcdef0123456789abcdef"
            ),
            issuer_id="linkskills-eval-runner-sealed-linux",
            env={},
        )
        self.assertFalse(result.ok)
        self.assertFalse(result.promoting)
        self.assertTrue(any("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY" in e for e in result.errors))

    def test_release_mode_repo_dev_key_fails_closed(self) -> None:
        result = validate_sealed_cert_preflight(
            mode=MODE_RELEASE,
            issuer_key=LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
            image=(
                "python@sha256:0123456789abcdef0123456789abcdef"
                "0123456789abcdef0123456789abcdef"
            ),
            issuer_id="linkskills-eval-runner-sealed-linux",
            env={},
        )
        self.assertFalse(result.ok)
        self.assertFalse(result.promoting)
        self.assertTrue(any("local dev key" in e for e in result.errors))

    def test_release_mode_floating_image_fails_closed(self) -> None:
        result = validate_sealed_cert_preflight(
            mode=MODE_RELEASE,
            issuer_key="ephemeral-process-only-release-key",
            image="python:3.12-slim",
            issuer_id="linkskills-eval-runner-sealed-linux",
            env={},
        )
        self.assertFalse(result.ok)
        self.assertFalse(result.promoting)
        self.assertTrue(any("digest-pinned" in e for e in result.errors))

    def test_release_mode_valid_external_key_and_digest_ok(self) -> None:
        image = (
            "python@sha256:0123456789abcdef0123456789abcdef"
            "0123456789abcdef0123456789abcdef"
        )
        result = validate_sealed_cert_preflight(
            mode=MODE_RELEASE,
            issuer_key="ephemeral-process-only-release-key",
            image=image,
            issuer_id="linkskills-eval-runner-sealed-linux",
            env={},
        )
        self.assertTrue(result.ok)
        self.assertTrue(result.promoting)
        self.assertEqual(result.image_digest, image.rsplit("@sha256:", 1)[-1])
        self.assertEqual(result.issuer_id, "linkskills-eval-runner-sealed-linux")

    def test_local_non_promoting_allows_dev_key_and_floating_image(self) -> None:
        result = validate_sealed_cert_preflight(
            mode=MODE_LOCAL_NON_PROMOTING,
            issuer_key="",
            image="",
            env={},
        )
        self.assertTrue(result.ok)
        self.assertTrue(result.non_promoting)
        self.assertFalse(result.promoting)
        self.assertEqual(result.image, "python:3.12-slim")

    def test_promoting_issuer_keys_exclude_dev_key(self) -> None:
        keys = promoting_issuer_keys(
            {
                "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY": LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
                "LINKSKILLS_EVAL_RUNNER_TRUSTED_KEYS": "good-key, "
                + LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
            }
        )
        self.assertEqual(keys, [b"good-key"])

    def test_non_promoting_classification_mapping(self) -> None:
        self.assertEqual(non_promoting_classification(True), "eval_pending")
        self.assertEqual(non_promoting_classification(False), "draft")


class SealedCertShellPreflightTests(unittest.TestCase):
    """Exercise scripts/run-sealed-linux-certify.sh fail-closed gates (no docker)."""

    SCRIPT = REPO_ROOT / "scripts" / "run-sealed-linux-certify.sh"

    def _run(self, env: dict[str, str], extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
        base = os.environ.copy()
        # Force dry-run / preflight-only path so tests never start docker.
        base["LINKSKILLS_SEALED_CERT_PREFLIGHT_ONLY"] = "1"
        base.update(env)
        # Clear inherited secrets that would accidentally satisfy release mode.
        for key in (
            "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
            "LINKSKILLS_SEALED_CERT_IMAGE",
            "LINKSKILLS_SEALED_CERT_MODE",
            "LINKSKILLS_CERT_NON_PROMOTING",
        ):
            if key not in env:
                base.pop(key, None)
        cmd = ["bash", str(self.SCRIPT), *(extra_args or [])]
        return subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=base,
            capture_output=True,
            text=True,
        )

    def test_shell_release_missing_key_exits_nonzero(self) -> None:
        pinned = (
            "python@sha256:0123456789abcdef0123456789abcdef"
            "0123456789abcdef0123456789abcdef"
        )
        proc = self._run({"LINKSKILLS_SEALED_CERT_IMAGE": pinned})
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("LINKSKILLS_EVAL_RUNNER_ISSUER_KEY", combined)
        self.assertNotIn(LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY, combined)

    def test_shell_release_repo_dev_key_exits_nonzero(self) -> None:
        pinned = (
            "python@sha256:0123456789abcdef0123456789abcdef"
            "0123456789abcdef0123456789abcdef"
        )
        proc = self._run(
            {
                "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY": LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
                "LINKSKILLS_SEALED_CERT_IMAGE": pinned,
            }
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("local dev key", combined)
        # Key material itself must never be logged.
        self.assertNotIn(LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY, combined)

    def test_shell_release_floating_image_exits_nonzero(self) -> None:
        proc = self._run(
            {
                "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY": "ephemeral-process-only-release-key",
                "LINKSKILLS_SEALED_CERT_IMAGE": "python:3.12-slim",
            }
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("digest-pinned", combined)
        self.assertNotIn("ephemeral-process-only-release-key", combined)

    def test_shell_local_non_promoting_preflight_ok(self) -> None:
        proc = self._run({}, extra_args=["--local-non-promoting"])
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        combined = proc.stdout + proc.stderr
        self.assertIn("local-non-promoting", combined)
        self.assertNotIn(LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY, combined)


class SealedCertDockerArgvSecretTests(unittest.TestCase):
    """Issuer key must never appear as a docker argv value (name-only --env)."""

    SCRIPT = REPO_ROOT / "scripts" / "run-sealed-linux-certify.sh"
    ENV_NAME = "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"
    # Distinct from LOCAL_DEV so release mode is valid; never assert presence in logs.
    RELEASE_KEY = "ws-c-argv-regression-issuer-key-not-for-production"
    PINNED_IMAGE = (
        "python@sha256:0123456789abcdef0123456789abcdef"
        "0123456789abcdef0123456789abcdef"
    )

    def _assert_issuer_key_not_in_docker_argv(self, argv: list[str], secret: str) -> None:
        """Fail if secret is an argv token or NAME=secret form."""
        for i, token in enumerate(argv):
            self.assertNotEqual(token, secret, msg=f"secret appears as argv[{i}]")
            self.assertFalse(
                token.startswith(f"{self.ENV_NAME}="),
                msg=f"issuer key passed as KEY=value in argv[{i}]",
            )
            self.assertNotIn(secret, token, msg=f"secret substring in argv[{i}]")
        # Name-only form: --env NAME (or -e NAME) with no following secret value.
        name_only_ok = False
        for i, token in enumerate(argv):
            if token in ("--env", "-e") and i + 1 < len(argv):
                nxt = argv[i + 1]
                if nxt == self.ENV_NAME:
                    name_only_ok = True
                    if i + 2 < len(argv):
                        self.assertNotEqual(argv[i + 2], secret)
                elif nxt.startswith(f"{self.ENV_NAME}="):
                    self.fail("issuer key must use name-only --env, not KEY=value")
            if token == f"--env={self.ENV_NAME}" or token == f"-e={self.ENV_NAME}":
                name_only_ok = True
            if token.startswith(f"--env={self.ENV_NAME}=") or token.startswith(
                f"-e={self.ENV_NAME}="
            ):
                self.fail("issuer key must use name-only --env, not --env=KEY=value")
        self.assertTrue(
            name_only_ok,
            msg="expected bare --env LINKSKILLS_EVAL_RUNNER_ISSUER_KEY in docker argv",
        )

    def _run_with_fake_docker(
        self,
        *,
        env: dict[str, str],
        extra_args: list[str] | None = None,
        secret: str,
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            argv_log = Path(tmp) / "docker-argv.json"
            docker_shim = bin_dir / "docker"
            docker_shim.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                f"json.dump(sys.argv[1:], open({str(argv_log)!r}, 'w', encoding='utf-8'))\n"
                "raise SystemExit(0)\n",
                encoding="utf-8",
            )
            docker_shim.chmod(0o755)

            base = os.environ.copy()
            base["PATH"] = f"{bin_dir}:{base.get('PATH', '')}"
            base["LINKSKILLS_SEALED_CERT_PREFLIGHT_ONLY"] = "0"
            base.update(env)
            for key in (
                "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
                "LINKSKILLS_SEALED_CERT_IMAGE",
                "LINKSKILLS_SEALED_CERT_MODE",
                "LINKSKILLS_CERT_NON_PROMOTING",
            ):
                if key not in env:
                    base.pop(key, None)

            proc = subprocess.run(
                ["bash", str(self.SCRIPT), *(extra_args or [])],
                cwd=str(REPO_ROOT),
                env=base,
                capture_output=True,
                text=True,
            )
            combined = proc.stdout + proc.stderr
            self.assertNotIn(secret, combined, msg="key material leaked to stdout/stderr")
            self.assertTrue(argv_log.is_file(), msg=combined)
            recorded = json.loads(argv_log.read_text(encoding="utf-8"))
            self.assertIsInstance(recorded, list)
            return proc, recorded

    def test_release_mode_docker_argv_uses_name_only_env_for_issuer_key(self) -> None:
        proc, argv = self._run_with_fake_docker(
            env={
                "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY": self.RELEASE_KEY,
                "LINKSKILLS_SEALED_CERT_IMAGE": self.PINNED_IMAGE,
                "LINKSKILLS_SEALED_CERT_MODE": "release",
            },
            secret=self.RELEASE_KEY,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertEqual(argv[0], "run")
        self._assert_issuer_key_not_in_docker_argv(argv, self.RELEASE_KEY)

    def test_local_non_promoting_docker_argv_uses_name_only_env_for_issuer_key(
        self,
    ) -> None:
        # Default fill exports LOCAL_DEV key into process env; must still be name-only.
        proc, argv = self._run_with_fake_docker(
            env={},
            extra_args=["--local-non-promoting"],
            secret=LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertEqual(argv[0], "run")
        self._assert_issuer_key_not_in_docker_argv(argv, LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY)


class NonPromotingCertifyCatalogTests(unittest.TestCase):
    def test_non_promoting_mode_cannot_write_sealed_release_evidence(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "certify_catalog",
            REPO_ROOT / "scripts" / "certify-catalog.py",
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "demo-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\nversion: 0.0.1\n---\n",
                encoding="utf-8",
            )
            suite = skill / "references"
            suite.mkdir(parents=True)
            (suite / "eval-suite.yaml").write_text(
                "schema_version: '0.1'\n"
                "suite_id: demo\n"
                "skill_id: demo-skill\n"
                "suite_version: 0.0.1\n"
                "skill_version_range: '>=0.0.1'\n"
                "pass_threshold: 0.8\n"
                "rubric:\n"
                "  - dimension: correctness\n"
                "    weight: 1.0\n"
                "scenarios:\n"
                "  - id: noop\n"
                "    case_type: golden\n"
                "    input: x\n"
                "    expected_criteria: ['x']\n",
                encoding="utf-8",
            )
            (root / "evidence" / "phase10").mkdir(parents=True)
            sealed_dir = root / "evidence" / "phase10" / "sealed"
            sealed_dir.mkdir(parents=True)
            marker = sealed_dir / "should-not-be-touched.json"
            marker.write_text("{}\n", encoding="utf-8")

            with mock.patch.dict(
                os.environ,
                {
                    "LINKSKILLS_CERT_NON_PROMOTING": "1",
                    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY": LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
                    "LINKSKILLS_EVAL_RUNNER_ISSUER_ID": "local-non-promoting-test",
                },
                clear=False,
            ):
                item = mod._evaluate_skill(
                    skill,
                    repo_root=root,
                    require_sealed=False,
                    isolation_ok=False,
                    toolchain=None,
                    non_promoting=True,
                )

            self.assertIn(item["classification"], {"draft", "eval_pending"})
            self.assertNotEqual(item["classification"], "usable")
            self.assertIsNone(item.get("evidence_path"))
            self.assertEqual(marker.read_text(encoding="utf-8"), "{}\n")
            # No new sealed release artifacts.
            self.assertEqual(sorted(p.name for p in sealed_dir.iterdir()), [marker.name])


class DevKeyCannotPromoteOverlayTests(unittest.TestCase):
    def test_dev_key_signed_receipt_cannot_promote_usable(self) -> None:
        from linkskills_eval_runner.receipt import build_execution_receipt, ToolCallRecord
        from lib.skill_runtime.certification_overlay import overlay_from_ledger

        os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"] = LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY
        os.environ["LINKSKILLS_EVAL_RUNNER_ISSUER_ID"] = "linkskills-eval-runner-test"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sealed = root / "evidence" / "phase10" / "sealed"
            sealed.mkdir(parents=True)
            receipt = build_execution_receipt(
                case_id="c1",
                skill_id="demo-skill",
                suite_id="s1",
                suite_hash="a" * 64,
                skill_release_hash="skill-release:" + "b" * 64,
                execution_profile_hash="c" * 64,
                toolchain={"tools": []},
                tool_calls=[
                    ToolCallRecord(
                        tool_id="text-echo",
                        version="1.0.0",
                        tool_hash="d" * 64,
                        adapter_kind="local_process",
                        argv=["hi"],
                        exit_code=0,
                        stdout_hash="e" * 64,
                        stderr_hash="f" * 64,
                    )
                ],
                exit_code=0,
                stdout="hi",
                stderr="",
                artifact_hashes=[],
                network_isolation="denied",
            )
            evidence = {
                "skill_id": "demo-skill",
                "certified": True,
                "skill_release_hash": receipt.skill_release_hash,
                "profile_hash": receipt.execution_profile_hash,
                "suite_hash": receipt.suite_hash,
                "cases": [
                    {
                        "case_id": "c1",
                        "status": "passed",
                        "evidence_source": "executor",
                        "execution_receipt": receipt.to_dict(),
                    }
                ],
            }
            path = sealed / "demo-skill-sealed.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            ledger = {
                "skills": {
                    "demo-skill": {
                        "classification": "usable",
                        "sealed_live_receipt_evidence": [
                            "evidence/phase10/sealed/demo-skill-sealed.json"
                        ],
                        "skill_release_hash": receipt.skill_release_hash,
                        "profile_hash": receipt.execution_profile_hash,
                        "suite_hash": receipt.suite_hash,
                        "tool_hash": "d" * 64,
                    }
                }
            }
            overlay = overlay_from_ledger(ledger, repo_root=root)
            self.assertEqual(overlay["demo-skill"], "draft")


if __name__ == "__main__":
    unittest.main()
