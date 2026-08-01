#!/usr/bin/env python3
"""Project-scoped Cursor canary contract: fragment, docs, and honesty evidence."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = REPO_ROOT / "configs" / "fragments" / "cursor-skills-canary.mcp.json.example"
CANARY_MD = REPO_ROOT / "docs" / "integrations" / "cursor" / "CANARY.md"
HANDOFF_MD = (
    REPO_ROOT / "docs" / "integrations" / "cursor" / "PACI-CLIENT-APPLICATION-HANDOFF.md"
)
ROLLBACK_MD = REPO_ROOT / "docs" / "integrations" / "cursor" / "ROLLBACK.md"
PHASE7 = REPO_ROOT / "evidence" / "phase7" / "cursor-canary-status.json"
CANARY_SET = REPO_ROOT / "evidence" / "phase1" / "canary-set.json"

PLATFORM_CANDIDATE = "421a35e97bc302be0f5e1f196d0a5e8d132f6fd8"
ENVELOPE_FROZEN = "platform.auth-token-envelope/0.1.0"
ENVELOPE_DRAFT = "0.1.3-draft"


class CursorCanaryContractTests(unittest.TestCase):
    def test_fragment_production_canary_contract(self) -> None:
        self.assertTrue(FRAGMENT.is_file(), f"missing fragment: {FRAGMENT}")
        doc = json.loads(FRAGMENT.read_text(encoding="utf-8"))
        canary = doc["mcpServers"]["linkskills-canary"]
        env = canary["env"]
        self.assertEqual(canary["command"], "python3")
        self.assertEqual(canary["args"], ["-m", "linkskills_mcp.paci_stdio_proxy"])
        self.assertEqual(env["LINKSKILLS_AUTH_MODE"], "production")
        self.assertEqual(env["LINKSKILLS_CANARY"], "1")
        self.assertEqual(env["LINKSKILLS_MCP_UPSTREAM"], "http")
        self.assertTrue(str(env["GATEWAY_URL"]).startswith("https://"))
        comment = doc["_comment"]
        self.assertIn(ENVELOPE_FROZEN, comment)
        self.assertIn("NOT 0.1.3-draft", comment)
        self.assertIn(PLATFORM_CANDIDATE, comment)
        self.assertIn("live_canary=false", comment)
        self.assertNotIn(ENVELOPE_DRAFT, comment.replace("NOT 0.1.3-draft", ""))

    def test_docs_pin_frozen_envelope_not_draft(self) -> None:
        for path in (CANARY_MD, HANDOFF_MD, ROLLBACK_MD):
            self.assertTrue(path.is_file(), f"missing doc: {path}")
            text = path.read_text(encoding="utf-8")
            self.assertIn(ENVELOPE_FROZEN, text)
            self.assertIn(PLATFORM_CANDIDATE, text)
            self.assertRegex(
                text,
                re.compile(r"certified candidate\s*[≠!=].*live", re.IGNORECASE),
            )
            # May mention draft only as superseded / NOT advertised.
            if ENVELOPE_DRAFT in text:
                self.assertTrue(
                    any(
                        marker in text.lower()
                        for marker in ("not", "supersedes", "obsolete", "not advertised")
                    ),
                    f"{path} mentions draft without negation/supersession context",
                )

    def test_phase7_honesty_markers(self) -> None:
        status = json.loads(PHASE7.read_text(encoding="utf-8"))
        self.assertIs(status["live_canary"], False)
        self.assertIs(status["global_cursor_mutation"], False)
        self.assertIs(status["certified_candidate_is_not_live"], True)
        self.assertEqual(status["paci_envelope_contract"], ENVELOPE_FROZEN)
        self.assertEqual(status["platform_certified_candidate"], PLATFORM_CANDIDATE)
        self.assertEqual(status["stage_completed"], 1)
        self.assertIn("not started", status["stages"]["8_multi_day_real_use"].lower())
        self.assertIs(status["paci_machine_token_client"]["live_proven"], False)

    def test_representative_canary_set_ten_skills(self) -> None:
        canary_set = json.loads(CANARY_SET.read_text(encoding="utf-8"))
        self.assertEqual(canary_set["selected_count"], 10)
        self.assertEqual(len(canary_set["skills"]), 10)
        self.assertIs(canary_set["live_canary"], False)
        self.assertEqual(
            canary_set["platform_certified_candidate"], PLATFORM_CANDIDATE
        )


if __name__ == "__main__":
    unittest.main()
