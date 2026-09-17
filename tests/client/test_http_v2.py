#!/usr/bin/env python3
"""Client fixture: HTTP v2 exact-byte client against the Gateway adapter."""

from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_client.http_v2 import HttpV2Client  # noqa: E402
from linkskills_client.mcp_v2 import McpV2Client, McpV2Error  # noqa: E402
from linkskills_core.provider_v2 import V2Provider  # noqa: E402
from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402
from linkskills_gateway.v2_http import identity_from_claims  # noqa: E402
from linkskills_mcp.v2_provider import ModernSkillsMcpServer  # noqa: E402


class ClientV2FixtureTests(unittest.TestCase):
    def test_mcp_and_http_share_exact_bytes(self) -> None:
        release = {
            "skill_id": "research",
            "version": "1.0.0",
            "family_id": "research",
            "resources": {"entrypoint": {"body": b"shared-bytes"}},
        }
        mcp_provider = V2Provider(
            lambda token: __import__(
                "linkskills_core.provider_v2", fromlist=["TrustedIdentity"]
            ).TrustedIdentity(
                "org-a",
                "actor-a",
                "lskills-api",
                frozenset({"skills.read"}),
                "binding",
            ),
            releases=[release],
            families=[{"family_id": "research", "display_name": "Research", "description": "R"}],
        )
        server = ModernSkillsMcpServer(mcp_provider)
        mcp = McpV2Client(server.handle_rpc, authorization="trusted")
        mcp.initialize()
        mcp_body, mcp_digest = mcp.read_exact("skills://release/research/1.0.0/resource/entrypoint")

        verifier = LocalUnsignedClaimsVerifier()
        http_provider = V2Provider(
            lambda token: identity_from_claims(
                verifier.verify(
                    token if token.lower().startswith("bearer ") else f"Bearer {token}",
                    request_payload={},
                    required_operation="skills_list",
                )
            ),
            releases=[release],
            families=[{"family_id": "research", "display_name": "Research", "description": "R"}],
        )
        httpd = create_server(
            "127.0.0.1",
            0,
            service=SkillsGatewayService(repo_root=REPO_ROOT, catalog_index={"skills": []}),
            verifier=verifier,
            v2_provider=http_provider,
        )
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            token = mint_test_bearer(
                {
                    "actor_id": "actor-v2",
                    "actor_kind": "human",
                    "org_id": "org-1",
                    "scopes": ["skills:read"],
                    "exp": int(time.time()) + 3600,
                }
            )
            http = HttpV2Client(
                f"http://127.0.0.1:{httpd.server_address[1]}",
                authorization=f"Bearer {token}",
            )
            http_body, http_digest = http.read_exact(
                "skills_release_resource_get",
                {"skill_id": "research", "version": "1.0.0", "resource_id": "entrypoint"},
            )
        finally:
            httpd.shutdown()
            httpd.server_close()
        self.assertEqual(mcp_body, http_body)
        self.assertEqual(mcp_digest, http_digest)
        with self.assertRaises(McpV2Error):
            mcp.read_exact(
                "skills://release/research/1.0.0/resource/entrypoint",
                expected_digest="sha256:" + "0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
