#!/usr/bin/env python3
"""Local invariants for SKILLS-W20 stage-readiness migration/runtime docs.

Validates:
- Manifest SHA-256 rows match on-disk SQL
- Preflight / backup / stage-gate docs exist and encode Platform-only live apply
- Hard blockers are stated when stage apply evidence is absent
- Evidence JSON does not invent stage apply or backup receipts
- Sealed Linux gap doc refuses macOS denied certification claims

Never connects to shared/stage/prod databases.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

MANIFEST = REPO_ROOT / "docs" / "migrations" / "MANIFEST-20260727-lskills-registry-v0.1.md"
PREFLIGHT = REPO_ROOT / "docs" / "migrations" / "PREFLIGHT-STAGE-READINESS.md"
BACKUP_TEMPLATE = REPO_ROOT / "docs" / "migrations" / "BACKUP-RECEIPT-TEMPLATE.md"
STAGE_GATE = REPO_ROOT / "docs" / "stage" / "MIGRATION-RUNTIME-STAGE-GATE.md"
CERT_READY = REPO_ROOT / "docs" / "stage" / "CERTIFICATION-RUNTIME-READINESS.md"
EVIDENCE_JSON = (
    REPO_ROOT / "evidence" / "stage-readiness" / "migration-preflight-local.json"
)
SEALED_GAP = REPO_ROOT / "evidence" / "stage-readiness" / "sealed-linux-evaluation-gap.md"

SHA256_ROW_RE = re.compile(
    r"`(?P<path>supabase/migrations/[^`]+)`\s*\|\s*`(?P<sha>[0-9a-f]{64})`",
    re.IGNORECASE,
)

PLATFORM_ONLY_PHRASES = (
    "LiNKplatform alone",
    "Platform alone",
)


class StagePreflightDocsTests(unittest.TestCase):
    def test_required_paths_exist(self) -> None:
        for path in (
            MANIFEST,
            PREFLIGHT,
            BACKUP_TEMPLATE,
            STAGE_GATE,
            CERT_READY,
            EVIDENCE_JSON,
            SEALED_GAP,
        ):
            self.assertTrue(path.is_file(), f"missing required path: {path}")

    def test_manifest_hashes_match_sql_bytes(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8")
        rows = list(SHA256_ROW_RE.finditer(text))
        self.assertGreaterEqual(len(rows), 8, "manifest must list full 000002–000009 set")
        for match in rows:
            rel = match.group("path")
            path = REPO_ROOT / rel
            self.assertTrue(path.is_file(), f"manifest references missing file: {rel}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                match.group("sha"),
                actual,
                f"manifest SHA-256 mismatch for {rel}",
            )

    def test_manifest_states_platform_only_live_apply(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8")
        self.assertTrue(
            any(p in text for p in PLATFORM_ONLY_PHRASES),
            "manifest must state Platform-only live apply",
        )
        self.assertIn("applies live", text.lower())

    def test_preflight_lists_hard_blockers_for_missing_stage_apply(self) -> None:
        text = PREFLIGHT.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertTrue(
            any(p in text for p in PLATFORM_ONLY_PHRASES),
            "preflight must reaffirm Platform-only live apply",
        )
        self.assertIn("hard blocker", lower)
        self.assertIn("stage db apply", lower)
        self.assertIn("backup receipt", lower)
        self.assertIn("B1", text)
        self.assertIn("B2", text)
        self.assertIn("B3", text)

    def test_backup_template_is_unfilled_placeholder(self) -> None:
        text = BACKUP_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("_PLATFORM_SUPPLIED_", text)
        self.assertIn("Hard blocker", text)
        self.assertNotRegex(
            text,
            r"Backup completed \(UTC\)\s*\|\s*`?20\d{2}-",
            "backup template must not invent completed backup timestamps",
        )

    def test_stage_gate_blocks_without_apply_receipt(self) -> None:
        text = STAGE_GATE.read_text(encoding="utf-8")
        self.assertIn("BLOCKED", text)
        self.assertIn("no platform stage apply receipt", text.lower())
        self.assertTrue(
            any(p in text for p in PLATFORM_ONLY_PHRASES),
            "stage gate must state Platform-only live apply",
        )

    def test_certification_readiness_separates_local_vs_sealed(self) -> None:
        text = CERT_READY.read_text(encoding="utf-8")
        self.assertIn("unproven", text.lower())
        self.assertIn("BLOCKED", text)
        self.assertIn("network_isolation=denied", text)

    def test_evidence_json_does_not_invent_stage_receipts(self) -> None:
        payload = json.loads(EVIDENCE_JSON.read_text(encoding="utf-8"))
        self.assertIsNone(payload.get("stage_db_apply_receipt"))
        self.assertIsNone(payload.get("backup_receipt"))
        self.assertFalse(payload.get("invented_stage_receipts"))
        self.assertTrue(payload["manifest"]["all_sha256_match"])
        self.assertEqual(payload["manifest"]["rows_checked"], 8)
        self.assertEqual(payload["live_apply_authority"], "LiNKplatform alone")
        self.assertFalse(
            payload["isolation_probe"]["certifiable_network_isolation_denied"]
        )
        blockers = payload.get("hard_blockers_open") or []
        self.assertTrue(
            any("stage_apply" in b for b in blockers),
            "evidence must keep stage apply blocker open",
        )
        do_not = payload.get("do_not_claim") or []
        self.assertTrue(
            any("stage_or_prod_migrations_applied" == c for c in do_not),
            "evidence must list stage/prod apply as do-not-claim",
        )

    def test_sealed_linux_gap_refuses_macos_denied_claim(self) -> None:
        text = SEALED_GAP.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("cannot", lower)
        self.assertIn("network_isolation=denied", text)
        self.assertIn("macos", lower)
        self.assertNotIn("certification achieved on this host", lower)


if __name__ == "__main__":
    unittest.main()
