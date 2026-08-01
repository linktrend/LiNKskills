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
TELEMETRY_MD = REPO_ROOT / "docs" / "integrations" / "cursor" / "TELEMETRY-CONTRACT.md"
PHASE7 = REPO_ROOT / "evidence" / "phase7" / "cursor-canary-status.json"
CANARY_SET = REPO_ROOT / "evidence" / "phase1" / "canary-set.json"
READINESS = (
    REPO_ROOT / "evidence" / "stage-readiness" / "cursor-canary-readiness.json"
)

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
        self.assertIn("global_cursor_mutation=false", comment)
        self.assertIn("TELEMETRY-CONTRACT.md", comment)
        self.assertNotIn(ENVELOPE_DRAFT, comment.replace("NOT 0.1.3-draft", ""))

    def test_docs_pin_frozen_envelope_not_draft(self) -> None:
        for path in (CANARY_MD, HANDOFF_MD, ROLLBACK_MD, TELEMETRY_MD):
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

    def test_telemetry_contract_events_privacy_idempotency(self) -> None:
        text = TELEMETRY_MD.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            re.compile(r"\*\*Live canary:\*\*\s*\*\*false\*\*", re.IGNORECASE),
        )
        self.assertRegex(
            text,
            re.compile(
                r"\*\*Global Cursor mutation:\*\*\s*\*\*false\*\*", re.IGNORECASE
            ),
        )
        self.assertIn("skill.run_started", text)
        self.assertIn("feedback.submitted", text)
        self.assertIn("[REDACTED]", text)
        self.assertIn("Idempotency-Key", text)
        self.assertIn("event_id", text)
        self.assertIn("LocalEventBuffer", text)
        self.assertIn("Brain", text)
        self.assertIn("~/.cursor/mcp.json", text)
        self.assertIn("blocked", text.lower())

    def test_phase7_honesty_markers(self) -> None:
        status = json.loads(PHASE7.read_text(encoding="utf-8"))
        self.assertIs(status["live_canary"], False)
        self.assertIs(status["global_cursor_mutation"], False)
        self.assertIs(status["certified_candidate_is_not_live"], True)
        self.assertEqual(status["paci_envelope_contract"], ENVELOPE_FROZEN)
        self.assertEqual(status["platform_certified_candidate"], PLATFORM_CANDIDATE)
        self.assertEqual(status["stage_completed"], 1)
        self.assertIn("not started", status["stages"]["8_multi_day_real_use"].lower())
        self.assertIn("blocked", status["stages"]["4_stage_run_telemetry"].lower())
        self.assertIs(status["paci_machine_token_client"]["live_proven"], False)
        self.assertIs(status["telemetry_contract"]["live_flush_proven"], False)
        self.assertTrue(status["telemetry_contract"]["documented"])

    def test_stage_readiness_honesty_markers(self) -> None:
        readiness = json.loads(READINESS.read_text(encoding="utf-8"))
        self.assertIs(readiness["live_canary"], False)
        self.assertIs(readiness["global_cursor_mutation"], False)
        self.assertIs(readiness["certified_candidate_is_not_live"], True)
        self.assertEqual(readiness["paci_envelope_contract"], ENVELOPE_FROZEN)
        self.assertEqual(readiness["platform_certified_candidate"], PLATFORM_CANDIDATE)
        self.assertEqual(readiness["stage_completed"], 1)
        gates = readiness["stage_gates"]
        self.assertEqual(gates["1_fake_contract"], "ready")
        self.assertEqual(gates["2_symlink_inspect_readonly"], "ready")
        for blocked_key in (
            "3_stage_readonly_discovery",
            "4_stage_run_telemetry",
            "5_packaged_tool_artifact",
            "8_multi_day_real_use",
        ):
            self.assertIn("blocked", gates[blocked_key])
        self.assertIs(readiness["telemetry_contract"]["live_flush_proven"], False)
        self.assertEqual(
            readiness["rollback_mode"],
            "project-scoped-disable-and-git-revert-only",
        )

    def test_representative_canary_set_ten_skills(self) -> None:
        canary_set = json.loads(CANARY_SET.read_text(encoding="utf-8"))
        self.assertEqual(canary_set["selected_count"], 10)
        self.assertEqual(len(canary_set["skills"]), 10)
        self.assertIs(canary_set["live_canary"], False)
        self.assertIs(canary_set["global_cursor_mutation"], False)
        self.assertEqual(
            canary_set["platform_certified_candidate"], PLATFORM_CANDIDATE
        )
        self.assertEqual(
            canary_set["telemetry_contract"],
            "docs/integrations/cursor/TELEMETRY-CONTRACT.md",
        )
        self.assertEqual(canary_set["stage_8_status"], "not_started_blocked")
        skill_ids = {row["skill_id"] for row in canary_set["skills"]}
        self.assertEqual(len(skill_ids), 10)
        for skill in canary_set["skills"]:
            self.assertGreaterEqual(int(skill["scenario_count"]), 3)

    def test_rollback_is_project_scoped_revert_only(self) -> None:
        text = ROLLBACK_MD.read_text(encoding="utf-8")
        self.assertIn("Revert-only", text)
        self.assertIn("project-scoped disable", text.lower())
        self.assertIn("~/.cursor/mcp.json", text)
        self.assertIn("never edit", text.lower())
        self.assertIn("git revert", text.lower())


if __name__ == "__main__":
    unittest.main()
