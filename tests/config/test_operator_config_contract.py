#!/usr/bin/env python3
"""Operator config contract: templates/runbooks must name the same PACI/ops env vars code parses."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT,
]
for path in PACKAGE_PATHS:
    sys.path.insert(0, str(path))

from linkskills_client import paci_token_client as token_mod  # noqa: E402
from linkskills_gateway import ops as ops_mod  # noqa: E402
from linkskills_gateway import paci_authenticator as auth_mod  # noqa: E402

OPERATOR_ARTIFACTS = (
    REPO_ROOT / "deploy" / "vps" / ".env.example",
    REPO_ROOT / "docs" / "deploy" / "GATEWAY-MCP-SERVICE-DEFINITION.md",
    REPO_ROOT / "docs" / "runbooks" / "PRODUCTION_OPERATIONS.md",
)

# Env names the Gateway PACI authenticator factory reads.
AUTHENTICATOR_ENV_VARS = (
    auth_mod.ENV_PACI_ISSUER,
    auth_mod.ENV_PACI_JWKS_URI,
    auth_mod.ENV_PACI_AUDIENCE,
    auth_mod.ENV_PACI_REQUIRED_SERVICE_SCOPES,
    auth_mod.ENV_PACI_INTROSPECTION_URL,
    auth_mod.ENV_PACI_INTROSPECTION_CLIENT_ID,
    auth_mod.ENV_PLATFORM_AUTHENTICATOR,
)

# Env names the Skills PACI token client reads.
TOKEN_CLIENT_ENV_VARS = (
    token_mod.ENV_CLIENT_ID,
    token_mod.ENV_TOKEN_ENDPOINT,
    token_mod.ENV_PRIVATE_KEY_FILE,
    token_mod.ENV_KID,
    token_mod.ENV_SCOPE,
    token_mod.ENV_RESOURCE_AUDIENCE,
    token_mod.ENV_AUTH_MODE,
)

# Ops / drain / shutdown names parsed by ops.py.
OPS_ENV_VARS = (
    ops_mod.ENV_SHUTDOWN_TIMEOUT_S,
    "LINKSKILLS_DRAIN",
)

# Drift sentinels — wrong historical names that must not reappear as the
# operator-facing canonical keys in this packet's artifacts.
FORBIDDEN_ALIASES = (
    "LINKSKILLS_PACI_JWKS_URL",
    "LINKSKILLS_PACI_TOKEN_URL",
    "LINKSKILLS_PACI_REQUIRED_SERVICE=",
    "LINKSKILLS_PACI_REQUIRED_SERVICE`",
    "LINKSKILLS_PACI_CLIENT_ASSERTION_KEY_SECRET_NAME",
)


class OperatorConfigContractTests(unittest.TestCase):
    def test_code_constants_use_uri_scopes_endpoint_and_private_key_file(self) -> None:
        self.assertEqual(auth_mod.ENV_PACI_JWKS_URI, "LINKSKILLS_PACI_JWKS_URI")
        self.assertEqual(
            auth_mod.ENV_PACI_REQUIRED_SERVICE_SCOPES,
            "LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES",
        )
        self.assertEqual(
            token_mod.ENV_TOKEN_ENDPOINT,
            "LINKSKILLS_PACI_TOKEN_ENDPOINT",
        )
        self.assertEqual(
            token_mod.ENV_PRIVATE_KEY_FILE,
            "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE",
        )

    def test_operator_artifacts_mention_every_runtime_env_name(self) -> None:
        required = (
            AUTHENTICATOR_ENV_VARS + TOKEN_CLIENT_ENV_VARS + OPS_ENV_VARS
        )
        missing_by_artifact = {}
        for artifact in OPERATOR_ARTIFACTS:
            self.assertTrue(artifact.is_file(), f"missing artifact: {artifact}")
            text = artifact.read_text(encoding="utf-8")
            missing = [name for name in required if name not in text]
            if missing:
                missing_by_artifact[str(artifact.relative_to(REPO_ROOT))] = missing
        self.assertEqual(
            missing_by_artifact,
            {},
            "operator artifacts drifted from runtime env parsers: "
            f"{missing_by_artifact}",
        )

    def test_operator_artifacts_reject_known_wrong_aliases(self) -> None:
        hits = {}
        for artifact in OPERATOR_ARTIFACTS:
            text = artifact.read_text(encoding="utf-8")
            found = [alias for alias in FORBIDDEN_ALIASES if alias in text]
            # REQUIRED_SERVICE without _SCOPES as a bare env token.
            if re.search(r"LINKSKILLS_PACI_REQUIRED_SERVICE(?!_SCOPES)", text):
                found.append("LINKSKILLS_PACI_REQUIRED_SERVICE(without _SCOPES)")
            if found:
                hits[str(artifact.relative_to(REPO_ROOT))] = found
        self.assertEqual(
            hits,
            {},
            f"forbidden env aliases still present: {hits}",
        )

    def test_env_example_assigns_canonical_keys(self) -> None:
        example = (REPO_ROOT / "deploy" / "vps" / ".env.example").read_text(
            encoding="utf-8"
        )
        for name in (
            "LINKSKILLS_PACI_JWKS_URI",
            "LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES",
            "LINKSKILLS_PACI_TOKEN_ENDPOINT",
            "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE",
            "LINKSKILLS_SHUTDOWN_TIMEOUT_S",
        ):
            self.assertRegex(
                example,
                rf"(?m)^{re.escape(name)}=",
                f".env.example must assign {name}",
            )


if __name__ == "__main__":
    unittest.main()
