#!/usr/bin/env python3
"""Focused tests for the ED-06 Server 01 Skills v2 candidate pack."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from server01_candidate import (  # noqa: E402
    LIVE_COMPOSE,
    PREVIOUS_IMAGE,
    Server01CandidateError,
    main,
    validate_overlay,
    validate_pack,
)


class Server01CandidateTests(unittest.TestCase):
    def test_pack_validates_against_current_checkout(self) -> None:
        receipt = validate_pack(ROOT)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["packet"], "ED-06")
        self.assertEqual(receipt["issue"], 328)
        self.assertIs(receipt["liveMutation"], False)
        self.assertEqual(receipt["hostedImageBuild"], "HOLD")
        self.assertEqual(receipt["previousImage"], PREVIOUS_IMAGE)
        self.assertEqual(receipt["contract"], "skills.api.v0.2")
        identity = receipt["sourceIdentity"]
        self.assertEqual(len(identity["commit"]), 40)
        self.assertEqual(len(identity["tree"]), 40)
        self.assertIn("LiNKskills", identity["origin"])
        self.assertTrue(receipt["overlayDigest"].startswith("sha256:"))

    def test_cli_validate_exits_zero(self) -> None:
        self.assertEqual(main(["validate", "--root", str(ROOT)]), 0)

    def test_cli_rejects_deploy_and_live_apply(self) -> None:
        self.assertEqual(main(["deploy"]), 2)
        self.assertEqual(main(["apply"]), 2)
        self.assertEqual(main(["compose-up"]), 2)

    def test_overlay_rejects_previous_digest_and_public_ports(self) -> None:
        data = json.loads((ROOT / "docs/integrations/server01/CANDIDATE.json").read_text())
        overlay = (ROOT / "docs/integrations/server01/compose.overlay.yml").read_text()
        poisoned = overlay.replace(
            "image: REPLACE_WITH_HOSTED_LINUX_AMD64_DIGEST",
            f"image: linktrend/linkskills@{PREVIOUS_IMAGE}",
        )
        with self.assertRaises(Server01CandidateError):
            validate_overlay(poisoned, data)
        public = overlay.replace("127.0.0.1:18798:8787", "0.0.0.0:18798:8787")
        with self.assertRaises(Server01CandidateError):
            validate_overlay(public, data)

    def test_overlay_rejects_root_and_missing_cap_drop(self) -> None:
        data = json.loads((ROOT / "docs/integrations/server01/CANDIDATE.json").read_text())
        overlay = (ROOT / "docs/integrations/server01/compose.overlay.yml").read_text()
        rooted = overlay.replace('user: "10002:10002"', 'user: "0:0"')
        with self.assertRaises(Server01CandidateError):
            validate_overlay(rooted, data)
        dropped = overlay.replace("cap_drop:\n      - ALL\n", "")
        with self.assertRaises(Server01CandidateError):
            validate_overlay(dropped, data)

    def test_secret_dsn_in_overlay_is_rejected(self) -> None:
        data = json.loads((ROOT / "docs/integrations/server01/CANDIDATE.json").read_text())
        overlay = (ROOT / "docs/integrations/server01/compose.overlay.yml").read_text()
        leaked = overlay + "\n      LINKSKILLS_DATABASE_URL: __LINKSKILLS_FORBIDDEN_SECRET__\n"
        with self.assertRaises(Server01CandidateError):
            validate_overlay(leaked, data)

    def test_missing_pack_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Server01CandidateError):
                validate_pack(Path(tmp))

    def test_handoff_names_untouched_live_compose(self) -> None:
        text = (ROOT / "docs/integrations/server01/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn(LIVE_COMPOSE, text)
        self.assertIn("CANDIDATE_NOT_DEPLOYED", text)
        self.assertIn("linkskills-mcp-v2", text)

    def test_overlay_command_does_not_duplicate_entrypoint_executable(self) -> None:
        overlay = (ROOT / "docs/integrations/server01/compose.overlay.yml").read_text()
        command = _overlay_command_args(overlay)
        self.assertEqual(command, ["--host", "0.0.0.0", "--port", "8787"])
        self.assertNotIn("linkskills-gateway", command)
        dockerfile = (ROOT / "docs/integrations/server01/Dockerfile.candidate").read_text()
        self.assertIn('ENTRYPOINT ["linkskills-gateway"]', dockerfile)
        self.assertIn("LINKSKILLS_REPO_ROOT=/opt/linkskills", dockerfile)
        self.assertIn("COPY catalog catalog", dockerfile)


def _overlay_command_args(overlay: str) -> list[str]:
    """Return compose ``command`` list items (fails if the executable is repeated)."""
    items: list[str] = []
    in_command = False
    for line in overlay.splitlines():
        if line.startswith("    command:"):
            in_command = True
            continue
        if not in_command:
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip().strip('"'))
            continue
        if stripped == "" or stripped.startswith("#"):
            continue
        break
    return items


if __name__ == "__main__":
    unittest.main()
