"""Fail-closed hosted sealed-evaluator contract (ED-03 admission, not certification)."""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO_ROOT))

from lib.skill_runtime.sealed_cert_mode import (
    HOSTED_CONTRACT_SCHEMA_ID,
    LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
    LOCAL_PRIVILEGED_SCRIPT_REL,
    MAX_HOSTED_ARTIFACT_BYTES,
    hosted_contract_authorizes_usable,
    payload_is_hosted_contract_document,
    refuse_local_privileged_docker_script,
    validate_hosted_sealed_evaluator_contract,
)

PINNED = (
    "python@sha256:0123456789abcdef0123456789abcdef"
    "0123456789abcdef0123456789abcdef"
)
COMMIT = "53a715278bbf333375774be4a9301fb5ba7e9667"
TREE = "810ddcfa2a41e501c8a38379f7fc44199991a38a"
TREE256 = "a" * 64


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_id": HOSTED_CONTRACT_SCHEMA_ID,
        "executor_kind": "hosted",
        "image": PINNED,
        "issuer_injection": "process-env-name-only",
        "network_isolation": "denied",
        "network_isolation_proof": "bwrap-unshare-net",
        "source_commit": COMMIT,
        "source_tree": TREE,
        "source_tree_sha256": TREE256,
        "artifact_retention": {
            "max_bytes": 1024,
            "max_age_hours": 24,
            "allowed_path_prefixes": ["evidence/end-to-end-delivery/ed-03/"],
        },
        "qualification_claim": "contract_only",
        "authorizes_usable": False,
        "privileged_docker": False,
        "local_script_transferred": False,
    }
    payload.update(overrides)
    return payload


class HostedContractUnitTests(unittest.TestCase):
    def test_valid_contract_admits_but_does_not_authorize_usable(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(_valid_payload(), env={})
        self.assertTrue(result.ok, msg=result.errors)
        self.assertFalse(result.authorizes_usable)
        self.assertFalse(hosted_contract_authorizes_usable(_valid_payload()))
        self.assertEqual(result.image_digest, PINNED.rsplit("@sha256:", 1)[-1])
        self.assertEqual(result.source_commit, COMMIT)
        self.assertEqual(result.source_tree, TREE)

    def test_floating_image_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(image="python:3.12-slim"), env={}
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("digest-pinned" in e for e in result.errors))

    def test_unproven_isolation_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(
                network_isolation="unproven",
                network_isolation_proof="allow_unproven",
            ),
            env={},
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("denied" in e for e in result.errors))

    def test_missing_source_identity_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(source_commit="", source_tree="", source_tree_sha256=""),
            env={},
        )
        self.assertFalse(result.ok)
        joined = " ".join(result.errors)
        self.assertIn("source_commit", joined)
        self.assertIn("source_tree", joined)
        self.assertIn("source_tree_sha256", joined)

    def test_privileged_docker_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(privileged_docker=True), env={}
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("privileged Docker" in e for e in result.errors))

    def test_local_script_transfer_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(
                local_script_transferred=True,
                local_script=LOCAL_PRIVILEGED_SCRIPT_REL,
            ),
            env={},
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("never be transferred" in e for e in result.errors))

    def test_embedded_secret_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(issuer_key="not-a-real-secret-value"), env={}
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("must not embed" in e for e in result.errors))

    def test_local_dev_issuer_key_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(),
            issuer_key=LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY,
            env={},
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("local dev issuer key" in e for e in result.errors))

    def test_unbounded_retention_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(
                artifact_retention={
                    "max_bytes": MAX_HOSTED_ARTIFACT_BYTES + 1,
                    "max_age_hours": 24,
                    "allowed_path_prefixes": ["evidence/end-to-end-delivery/ed-03/"],
                }
            ),
            env={},
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("max_bytes exceeds" in e for e in result.errors))

    def test_phase10_sealed_prefix_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(
                artifact_retention={
                    "max_bytes": 1024,
                    "max_age_hours": 1,
                    "allowed_path_prefixes": ["evidence/phase10/sealed/"],
                }
            ),
            env={},
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("phase10/sealed" in e for e in result.errors))

    def test_usable_claim_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(qualification_claim="usable", authorizes_usable=True),
            env={},
        )
        self.assertFalse(result.ok)
        self.assertFalse(result.authorizes_usable)
        self.assertTrue(any("must not claim usable" in e for e in result.errors))

    def test_server01_target_fails_closed(self) -> None:
        result = validate_hosted_sealed_evaluator_contract(
            _valid_payload(target="server01"), env={}
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("server01" in e for e in result.errors))

    def test_payload_document_helper(self) -> None:
        self.assertTrue(payload_is_hosted_contract_document(_valid_payload()))
        self.assertFalse(payload_is_hosted_contract_document({"certified": True}))


class LocalPrivilegedScriptRefuseTests(unittest.TestCase):
    def test_default_env_allows_local_script(self) -> None:
        ok, errors = refuse_local_privileged_docker_script(env={})
        self.assertTrue(ok)
        self.assertEqual(errors, ())

    def test_hosted_kind_refuses_local_script(self) -> None:
        ok, errors = refuse_local_privileged_docker_script(
            {"LINKSKILLS_SEALED_EXECUTOR_KIND": "hosted"}
        )
        self.assertFalse(ok)
        self.assertTrue(any("hosted" in e for e in errors))

    def test_server01_target_refuses_local_script(self) -> None:
        ok, errors = refuse_local_privileged_docker_script(
            {"LINKSKILLS_SEALED_TARGET": "server01"}
        )
        self.assertFalse(ok)
        self.assertTrue(any("Server01/VPS" in e for e in errors))

    def test_production_issuer_flag_refuses_local_script(self) -> None:
        ok, errors = refuse_local_privileged_docker_script(
            {"LINKSKILLS_USE_PRODUCTION_ISSUER": "1"}
        )
        self.assertFalse(ok)
        self.assertTrue(any("production issuer" in e for e in errors))


class LocalScriptHostedFlagShellTests(unittest.TestCase):
    SCRIPT = REPO_ROOT / "scripts" / "run-sealed-linux-certify.sh"

    def _run(self, env: dict[str, str], extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
        base = os.environ.copy()
        base["LINKSKILLS_SEALED_CERT_PREFLIGHT_ONLY"] = "1"
        for key in (
            "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
            "LINKSKILLS_SEALED_CERT_IMAGE",
            "LINKSKILLS_SEALED_CERT_MODE",
            "LINKSKILLS_CERT_NON_PROMOTING",
            "LINKSKILLS_SEALED_EXECUTOR_KIND",
            "LINKSKILLS_SEALED_TARGET",
            "LINKSKILLS_HOSTED_SEALED_EVALUATOR",
            "LINKSKILLS_USE_PRODUCTION_ISSUER",
        ):
            base.pop(key, None)
        base.update(env)
        return subprocess.run(
            ["bash", str(self.SCRIPT), *(extra or [])],
            cwd=str(REPO_ROOT),
            env=base,
            capture_output=True,
            text=True,
        )

    def test_hosted_flag_exits_nonzero(self) -> None:
        proc = self._run({}, extra=["--hosted"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("local privileged Docker only", proc.stderr + proc.stdout)

    def test_hosted_kind_env_exits_nonzero_without_docker(self) -> None:
        proc = self._run(
            {
                "LINKSKILLS_SEALED_EXECUTOR_KIND": "hosted",
                "LINKSKILLS_SEALED_CERT_IMAGE": PINNED,
                "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY": "ephemeral-process-only-release-key",
            }
        )
        self.assertNotEqual(proc.returncode, 0)
        combined = proc.stdout + proc.stderr
        self.assertIn("hosted", combined)
        self.assertNotIn("ephemeral-process-only-release-key", combined)

    def test_local_non_promoting_still_ok(self) -> None:
        proc = self._run({}, extra=["--local-non-promoting"])
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("local-non-promoting", proc.stdout + proc.stderr)


class HostedContractDocTests(unittest.TestCase):
    def test_contract_doc_exists_and_refuses_transfer(self) -> None:
        path = REPO_ROOT / "docs" / "stage" / "HOSTED-SEALED-EVALUATOR-CONTRACT.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("linkskills.hosted-sealed-evaluator/0.1.0", text)
        self.assertIn("server01", text.lower())
        self.assertIn("vps", text.lower())
        self.assertIn("never", text.lower())
        self.assertIn("process-env-name-only", text)
        self.assertIn("network_isolation", text)
        self.assertIn("usable", text)
        ready = (
            REPO_ROOT / "docs" / "stage" / "CERTIFICATION-RUNTIME-READINESS.md"
        ).read_text(encoding="utf-8")
        self.assertIn("HOSTED-SEALED-EVALUATOR-CONTRACT.md", ready)
        self.assertIn("unproven", ready.lower())
        self.assertIn("BLOCKED", ready)
        self.assertIn("network_isolation=denied", ready)


if __name__ == "__main__":
    unittest.main()
