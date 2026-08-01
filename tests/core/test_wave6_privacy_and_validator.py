#!/usr/bin/env python3
"""Wave-6 privacy, isolation-cert, and validator schema routing tests."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_core.payload_guard import (  # noqa: E402
    PayloadValidationError,
    allowlist_and_redact,
    reject_forbidden_privacy,
    sanitize_result_payload,
)
from linkskills_core.retention import REDACTED  # noqa: E402


class RecursivePrivacyTests(unittest.TestCase):
    def test_rejects_nested_conversation(self) -> None:
        with self.assertRaises(PayloadValidationError):
            reject_forbidden_privacy(
                {"notes": {"conversation": "private chat"}, "run_id": "r1"},
                allowed_keys={"notes", "run_id"},
            )

    def test_rejects_nested_prompt_and_brain(self) -> None:
        with self.assertRaises(PayloadValidationError):
            reject_forbidden_privacy(
                {"details": {"prompt": "system", "brain_data": {"x": 1}}},
                allowed_keys={"details"},
            )

    def test_redacts_unknown_content_bearing(self) -> None:
        cleaned = sanitize_result_payload(
            {"status": "ok", "blob_text": "should hide", "nested": {"raw_output": "x"}}
        )
        self.assertEqual(cleaned["status"], "ok")
        self.assertNotEqual(cleaned["blob_text"], "should hide")
        self.assertEqual(cleaned["nested"]["raw_output"], REDACTED)

    def test_allowlist_preserves_structural_output_key(self) -> None:
        result = allowlist_and_redact(
            {"run_id": "r1", "output": {"step": 1, "conversation": "nope"}},
            allowed_keys={"run_id", "output"},
            require_keys={"run_id"},
        )
        # Nested conversation must not survive; structural output key remains.
        self.assertIn("output", result)
        self.assertEqual(result["output"]["conversation"], REDACTED)
        self.assertEqual(result["output"]["step"], 1)


class ValidatorSchemaRoutingTests(unittest.TestCase):
    def test_contract_fixtures_via_validator(self) -> None:
        import validator as skill_validator

        ok, errors = skill_validator.validate_contract_fixtures(REPO_ROOT)
        self.assertTrue(ok, errors)


if __name__ == "__main__":
    unittest.main()
