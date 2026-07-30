#!/usr/bin/env python3
"""Regression: AuthClaims 1.1.0 / package 0.2.2 pin must stay internally consistent."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import (  # noqa: E402
    CLAIM_CONTRACT_VERSION,
    EXPECTED_SCHEMA_BYTES_SHA256,
    EXPECTED_SCHEMA_CONTENT_HASH,
    PLATFORM_CONTRACTS_PACKAGE,
    SCHEMA_PATH,
    verify_frozen_auth_claims_schema,
    _canonicalize_json,
)

EXPECTED_CONTRACT = "platform.auth-claims/1.1.0"
EXPECTED_PACKAGE = "0.2.2"
EXPECTED_SCHEMA_SHA = (
    "c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1"
)
EXPECTED_CONTENT_HASH = (
    "fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567"
)


class AuthClaimsPinConsistencyTests(unittest.TestCase):
    def test_auth_module_constants_match_authoritative_pin(self) -> None:
        self.assertEqual(CLAIM_CONTRACT_VERSION, EXPECTED_CONTRACT)
        self.assertEqual(PLATFORM_CONTRACTS_PACKAGE, EXPECTED_PACKAGE)
        self.assertEqual(EXPECTED_SCHEMA_BYTES_SHA256, EXPECTED_SCHEMA_SHA)
        self.assertEqual(EXPECTED_SCHEMA_CONTENT_HASH, EXPECTED_CONTENT_HASH)

    def test_vendored_schema_bytes_and_content_hash(self) -> None:
        self.assertTrue(SCHEMA_PATH.is_file(), msg=str(SCHEMA_PATH))
        raw = SCHEMA_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), EXPECTED_SCHEMA_SHA)
        content = hashlib.sha256(
            _canonicalize_json(json.loads(raw.decode("utf-8"))).encode("utf-8")
        ).hexdigest()
        self.assertEqual(content, EXPECTED_CONTENT_HASH)
        meta = verify_frozen_auth_claims_schema()
        self.assertEqual(meta["contract"], EXPECTED_CONTRACT)
        self.assertEqual(meta["package"], EXPECTED_PACKAGE)
        self.assertEqual(meta["schema_bytes_sha256"], EXPECTED_SCHEMA_SHA)
        self.assertEqual(meta["content_hash"], EXPECTED_CONTENT_HASH)

    def test_consumer_pin_doc_matches_constants(self) -> None:
        pin = (
            REPO_ROOT
            / "docs"
            / "contracts"
            / "frozen"
            / "platform-auth-claims-v1.1.0.CONSUMER-PIN.md"
        ).read_text(encoding="utf-8")
        self.assertIn(f"`{EXPECTED_CONTRACT}`", pin)
        self.assertIn(f"`{EXPECTED_PACKAGE}`", pin)
        self.assertIn(f"`{EXPECTED_SCHEMA_SHA}`", pin)
        self.assertIn(f"`{EXPECTED_CONTENT_HASH}`", pin)
        # Must not present superseded package as the live 1.1 pin.
        self.assertNotRegex(
            pin,
            r"Platform package \| `@linktrend/platform-contracts` `0\.2\.1`",
        )

    def test_openclaw_fragment_matches_constants(self) -> None:
        fragment = json.loads(
            (
                REPO_ROOT
                / "configs"
                / "fragments"
                / "openclaw-skills.mcp.json.fragment"
            ).read_text(encoding="utf-8")
        )
        auth = fragment["auth"]
        self.assertEqual(auth["claim_contract"], EXPECTED_CONTRACT)
        self.assertEqual(auth["platform_contracts_package"], EXPECTED_PACKAGE)
        self.assertEqual(auth["schema_bytes_sha256"], EXPECTED_SCHEMA_SHA)
        self.assertEqual(auth["content_hash"], EXPECTED_CONTENT_HASH)
        self.assertIn("v1.1.0.CONSUMER-PIN.md", auth["consumer_pin"])

    def test_accept_fixtures_metadata_matches_live_pin(self) -> None:
        fixtures_dir = (
            REPO_ROOT / "packages" / "contracts" / "fixtures" / "platform-claims"
        )
        for path in sorted(fixtures_dir.glob("accept-*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                data["claims"]["claimContractVersion"],
                EXPECTED_CONTRACT,
                msg=path.name,
            )
            if "platformContract" in data:
                self.assertEqual(data["platformContract"], EXPECTED_CONTRACT, msg=path.name)
            if "platformContractsPackage" in data:
                self.assertEqual(
                    data["platformContractsPackage"], EXPECTED_PACKAGE, msg=path.name
                )

    def test_no_stale_live_0_2_1_pin_in_production_surfaces(self) -> None:
        """Live production surfaces must not advertise 0.2.1 for AuthClaims 1.1."""
        live_paths = [
            REPO_ROOT / "packages" / "gateway" / "linkskills_gateway" / "auth.py",
            REPO_ROOT / "docs" / "integrations" / "openclaw" / "HANDOFF.md",
            REPO_ROOT
            / "docs"
            / "contracts"
            / "frozen"
            / "platform-auth-claims-v1.1.0.CONSUMER-PIN.md",
            REPO_ROOT / "configs" / "fragments" / "openclaw-skills.mcp.json.fragment",
        ]
        stale = re.compile(
            r"platform-contracts@0\.2\.1|platform_contracts_package.: .0\.2\.1."
            r"|PLATFORM_CONTRACTS_PACKAGE = \"0\.2\.1\""
        )
        for path in live_paths:
            text = path.read_text(encoding="utf-8")
            # Historical prior-pin mentions of 0.2.1 are allowed only with explicit
            # historical/superseded wording in the 1.1 consumer pin doc.
            if path.name.endswith("v1.1.0.CONSUMER-PIN.md"):
                self.assertIn("0.2.2", text)
                self.assertIn("historical", text.lower())
                continue
            self.assertIsNone(
                stale.search(text),
                msg=f"stale 0.2.1 live pin in {path.relative_to(REPO_ROOT)}",
            )


if __name__ == "__main__":
    unittest.main()
