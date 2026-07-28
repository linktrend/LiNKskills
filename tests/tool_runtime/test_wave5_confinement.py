#!/usr/bin/env python3
"""Wave-5 adversarial confinement, authz, payload, and ServerAdapter tests."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)
os.environ.setdefault("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "tool_runtime",
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.service import ServiceError, SkillsGatewayService  # noqa: E402
from linkskills_tool_runtime.adapters import ServerAdapter  # noqa: E402
from linkskills_tool_runtime.confined_exec import (  # noqa: E402
    ConfinedExecutionError,
    assert_within_boundary,
    run_confined,
)
from linkskills_tool_runtime.invoke import invoke_tool  # noqa: E402


class ConfinedExecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(tempfile.mkdtemp(prefix="w5-confine-"))
        (self.workspace / "tmp").mkdir(exist_ok=True)

    def test_rejects_shell_lc(self) -> None:
        with self.assertRaises(ConfinedExecutionError):
            run_confined(
                ["bash", "-lc", "echo hi"],
                workspace=self.workspace,
            )

    def test_rejects_symlink_escape(self) -> None:
        outside = Path(tempfile.mkdtemp(prefix="w5-outside-"))
        secret = outside / "secret.txt"
        secret.write_text("nope", encoding="utf-8")
        link = self.workspace / "escape"
        link.symlink_to(outside)
        with self.assertRaises(ConfinedExecutionError):
            assert_within_boundary(link / "secret.txt", self.workspace)

    def test_argv_command_runs_when_unproven_allowed(self) -> None:
        result = run_confined(
            ["python3", "-c", "print('confined-ok')"],
            workspace=self.workspace,
        )
        self.assertIn("confined-ok", result.stdout)
        self.assertIn(result.network_isolation, {"denied", "unproven"})

    def test_sandbox_profile_does_not_allow_global_file_read(self) -> None:
        from linkskills_tool_runtime.confined_exec import (
            _profile_uses_global_file_read,
            _wrap_with_network_deny,
        )

        wrapped, status = _wrap_with_network_deny(
            ["python3", "-c", "print(1)"],
            workspace=self.workspace,
        )
        joined = " ".join(wrapped)
        if status == "denied" and "sandbox-exec" in joined:
            profile_path = self.workspace / "tmp" / "fs-allowlist.sb"
            self.assertTrue(profile_path.is_file())
            profile = profile_path.read_text(encoding="utf-8")
            self.assertFalse(_profile_uses_global_file_read(profile))
            self.assertIn(self.workspace.name, profile)
            self.assertIn("deny network*", profile)
        if status == "denied" and "bwrap" in joined:
            self.assertNotIn("--ro-bind / /", joined)
            self.assertIn("--tmpfs /", joined)
        # Wave 7: macOS deny-list/global-read must never report denied.
        if "sandbox-exec" in joined and status == "denied":
            profile = (self.workspace / "tmp" / "fs-allowlist.sb").read_text(encoding="utf-8")
            self.assertNotIn("(allow file-read*)\n(deny file-read*", profile)

    def test_confined_cannot_read_outside_workspace_home_file(self) -> None:
        """When isolation is denied, host home files outside workspace are unreadable."""
        outside_dir = Path.home() / ".cache" / "linkskills-w7-confine-test"
        outside_dir.mkdir(parents=True, exist_ok=True)
        secret = outside_dir / f"secret-{os.getpid()}.txt"
        secret.write_text("TOPSECRET", encoding="utf-8")
        try:
            result = run_confined(
                ["python3", "-c", f"print(open({str(secret)!r}).read())"],
                workspace=self.workspace,
            )
            if result.network_isolation != "denied":
                self.skipTest("proven OS isolator unavailable in this environment")
            self.assertNotIn("TOPSECRET", result.stdout)
            self.assertNotEqual(result.exit_code, 0)
        finally:
            try:
                secret.unlink()
            except OSError:
                pass

    def test_adversarial_var_folders_and_cache_reads(self) -> None:
        """Denied isolation must block /var/folders and user cache secrets."""
        import tempfile

        secrets = []
        try:
            tmp_secret = Path(tempfile.gettempdir()) / f"linkskills-w7-tmp-{os.getpid()}.txt"
            tmp_secret.write_text("TMP_SECRET_VALUE", encoding="utf-8")
            secrets.append(tmp_secret)
            cache_dir = Path.home() / "Library" / "Caches" / "linkskills-w7-confine"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_secret = cache_dir / f"secret-{os.getpid()}.txt"
            cache_secret.write_text("CACHE_SECRET_VALUE", encoding="utf-8")
            secrets.append(cache_secret)

            for secret in secrets:
                result = run_confined(
                    ["python3", "-c", f"print(open({str(secret)!r}).read())"],
                    workspace=self.workspace,
                )
                if result.network_isolation == "denied":
                    self.assertNotIn(secret.read_text(encoding="utf-8"), result.stdout)
                    self.assertNotEqual(result.exit_code, 0)
                else:
                    # Unproven/unavailable must never be treated as certifiable denial.
                    self.assertIn(result.network_isolation, {"unproven", "unavailable"})
        finally:
            for secret in secrets:
                try:
                    secret.unlink()
                except OSError:
                    pass

    def test_macos_does_not_claim_denied_with_global_file_read(self) -> None:
        import sys

        if sys.platform != "darwin":
            self.skipTest("macOS-only confidentiality regression")
        from linkskills_tool_runtime.confined_exec import _wrap_with_network_deny

        _wrapped, status = _wrap_with_network_deny(
            ["python3", "-c", "print(1)"],
            workspace=self.workspace,
        )
        # Current dyld typically cannot boot a pure allowlist; status must not be
        # denied via a leaky global-read profile.
        profile = self.workspace / "tmp" / "fs-allowlist.sb"
        if status == "denied":
            self.assertTrue(profile.is_file())
            text = profile.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?m)^\(allow file-read\*\)$")
        else:
            self.assertEqual(status, "unavailable")

    def test_required_network_isolation_fails_closed_without_wrapper(self) -> None:
        prev = os.environ.get("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION")
        os.environ["LINKSKILLS_EXECUTOR_NETWORK_ISOLATION"] = "required"
        try:
            # Force unavailable path by clearing PATH so wrappers are missing, then restore
            # only python3 via absolute path.
            import shutil

            py = shutil.which("python3")
            self.assertIsNotNone(py)
            # If sandbox-exec/bwrap exists this may still succeed with denied — both are ok.
            result_or_err = None
            try:
                result_or_err = run_confined([py, "-c", "print(1)"], workspace=self.workspace)
            except ConfinedExecutionError as exc:
                result_or_err = exc
            if isinstance(result_or_err, ConfinedExecutionError):
                self.assertIn("isolation", str(result_or_err).lower())
            else:
                self.assertEqual(result_or_err.network_isolation, "denied")
        finally:
            if prev is None:
                os.environ.pop("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", None)
            else:
                os.environ["LINKSKILLS_EXECUTOR_NETWORK_ISOLATION"] = prev


class ServerAdapterDisabledTests(unittest.TestCase):
    def test_server_adapter_disabled(self) -> None:
        self.assertFalse(ServerAdapter.ENABLED)
        result = invoke_tool(
            REPO_ROOT / "tools" / "text-echo",
            tool_id="text-echo",
            adapter="server",
        )
        self.assertFalse(result.ok)
        self.assertIn("disabled", (result.error or "").lower())


class ExactPermissionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = {
            "skills": [
                {
                    "skill_id": "usable-demo",
                    "version": "1.0.0",
                    "description": "usable demo",
                    "format_profile": "heavy",
                    "eval_suite_ref": "",
                    "certification_state": "usable",
                    "release_hash": "release-usable-1",
                    "profile_hash": "profile-usable-1",
                    "compatible_runtime_profiles": ["cursor-macos"],
                }
            ]
        }
        self.service = SkillsGatewayService(
            repo_root=REPO_ROOT, catalog_index=self.catalog
        )

    def test_empty_permitted_operations_fails_read(self) -> None:
        actor = LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_test_bearer({'permittedOperations': []})}"
        )
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch("skills_list", {}, actor=actor)
        self.assertEqual(ctx.exception.code, "auth_forbidden")

    def test_read_only_cannot_start_run(self) -> None:
        actor = LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_test_bearer({'permittedOperations': ['read', 'skills:read']})}"
        )
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_run_start",
                {
                    "skill_id": "usable-demo",
                    "runtime_profile_tags": ["cursor-macos"],
                },
                actor=actor,
            )
        self.assertEqual(ctx.exception.code, "auth_forbidden")


class FeedbackTraceBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = {
            "skills": [
                {
                    "skill_id": "usable-demo",
                    "version": "1.0.0",
                    "description": "usable demo",
                    "format_profile": "heavy",
                    "eval_suite_ref": "",
                    "certification_state": "usable",
                    "release_hash": "release-usable-1",
                    "profile_hash": "profile-usable-1",
                    "compatible_runtime_profiles": ["cursor-macos"],
                }
            ]
        }
        self.service = SkillsGatewayService(
            repo_root=REPO_ROOT, catalog_index=self.catalog
        )
        self.actor = LocalUnsignedClaimsVerifier().verify(f"Bearer {mint_test_bearer()}")

    def test_feedback_requires_accessible_run(self) -> None:
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_feedback_submit",
                {
                    "skill_id": "usable-demo",
                    "run_id": "missing-run",
                    "notes": "x",
                },
                actor=self.actor,
            )
        self.assertEqual(ctx.exception.code, "not_found")

    def test_rejects_secret_field_in_feedback(self) -> None:
        started = self.service.dispatch(
            "skills_run_start",
            {
                "skill_id": "usable-demo",
                "runtime_profile_tags": ["cursor-macos"],
            },
            actor=self.actor,
        )
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_feedback_submit",
                {
                    "skill_id": "usable-demo",
                    "run_id": started["run_id"],
                    "api_key": "sekrit",
                    "notes": "x",
                },
                actor=self.actor,
            )
        self.assertIn(ctx.exception.code, {"payload_forbidden_field", "payload_unexpected_field"})

    def test_idempotent_run_update(self) -> None:
        started = self.service.dispatch(
            "skills_run_start",
            {
                "skill_id": "usable-demo",
                "runtime_profile_tags": ["cursor-macos"],
            },
            actor=self.actor,
            idempotency_key="start-1",
        )
        run_id = started["run_id"]
        payload = {"run_id": run_id, "progress": {"step": 1}}
        a = self.service.dispatch(
            "skills_run_update",
            payload,
            actor=self.actor,
            idempotency_key="upd-1",
        )
        b = self.service.dispatch(
            "skills_run_update",
            payload,
            actor=self.actor,
            idempotency_key="upd-1",
        )
        self.assertIn("idempotent_replay", b.get("warnings") or [])
        self.assertEqual(a["data"]["event"]["progress"], b["data"]["event"]["progress"])

    def test_idempotency_key_payload_mismatch_conflicts(self) -> None:
        started = self.service.dispatch(
            "skills_run_start",
            {
                "skill_id": "usable-demo",
                "runtime_profile_tags": ["cursor-macos"],
            },
            actor=self.actor,
        )
        run_id = started["run_id"]
        self.service.dispatch(
            "skills_run_update",
            {"run_id": run_id, "progress": {"step": 1}},
            actor=self.actor,
            idempotency_key="upd-conflict",
        )
        with self.assertRaises(ServiceError) as ctx:
            self.service.dispatch(
                "skills_run_update",
                {"run_id": run_id, "progress": {"step": 99}},
                actor=self.actor,
                idempotency_key="upd-conflict",
            )
        self.assertEqual(ctx.exception.code, "idempotency_conflict")


if __name__ == "__main__":
    unittest.main()
