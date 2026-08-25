import unittest
from linkskills_client.mcp_v2 import McpV2Client, McpV2Error
from linkskills_mcp.v2_provider import ModernSkillsMcpServer, RESOURCE_OPERATIONS, TOOLS, TrustedIdentity, V2Provider

def verifier(token):
    if token != "trusted": raise ValueError("bad token")
    return TrustedIdentity("org-a", "actor-a", "lskills-api", frozenset({"skills.read"}), "runtime-binding")

class V2ProviderTests(unittest.TestCase):
    def setUp(self):
        self.p = V2Provider(verifier, catalog_version="catalogue-42")
        self.base = {"protocol_version":"2026-07-28", "authorization":"trusted"}
    def call(self, operation, **extra): return self.p.handle(dict(self.base, operation=operation, **extra))
    def test_resource_first_and_restricted_tools(self):
        self.assertEqual(len(self.p.resources()), 13); self.assertEqual(len(self.p.tools()), 6)
        self.assertEqual({x["name"] for x in self.p.resources()}, set(RESOURCE_OPERATIONS)); self.assertTrue(set(TOOLS).isdisjoint(RESOURCE_OPERATIONS))
    def test_trusted_identity_cannot_be_payload_overridden(self):
        result = self.call("skills_catalog_list", org_id="other", actor_id="other", capabilities=["admin"])
        self.assertTrue(result["ok"])
        for authorization, expected in ((None,"auth_required"),("forged","auth_invalid")):
            self.assertEqual(self.p.handle({"protocol_version":"2026-07-28","authorization":authorization,"operation":"skills_catalog_list"})["error"], expected)
        bad = V2Provider(lambda _: TrustedIdentity("o","a","wrong",frozenset({"skills.read"}),"b"))
        self.assertEqual(bad.handle(dict(self.base, operation="skills_catalog_list"))["error"], "forbidden")
    def test_catalog_has_snapshot_but_release_is_exact(self):
        catalog = self.call("skills_catalog_list", limit=2); self.assertTrue(catalog["ok"]); self.assertIn("snapshot_id", catalog)
        self.assertTrue(self.call("skills_catalog_search")["ok"])
        self.assertEqual(self.call("skills_release_describe")["error"], "exact_release_required")
        release = self.call("skills_release_describe", skill_id="safe", version="1.0.0", cursor=catalog["cursor"]); self.assertTrue(release["ok"])
    def test_cursor_protocol_legacy_and_bounds_fail_closed(self):
        for extra, expected in (({"cursor":"bad"},"cursor_snapshot_mismatch"),({"cursor":"snapshot:wrong:0"},"cursor_snapshot_mismatch"),({"limit":101},"validation_failed"),({"session_id":"x"},"session_not_supported"),({"protocol_version":"2024-11-05"},"contract_incompatible")):
            self.assertEqual(self.p.handle(dict(self.base, operation="skills_catalog_list", **extra))["error"], expected)
        self.assertEqual(self.call("skills_run_start")["error"], "legacy_execution_disabled")
        self.assertEqual(self.call("skills_tool_invoke")["error"], "legacy_execution_disabled")
    def test_modern_rpc_is_sessionless(self):
        server = ModernSkillsMcpServer(self.p)
        self.assertEqual(server.handle_rpc({"id":1,"method":"initialize"})["error"]["message"], "session_not_supported")
        listed = server.handle_rpc({"id":2,"method":"resources/list","params":{"authorization":"trusted"}})
        self.assertEqual(len(listed["result"]["resources"]),13)


class GovernedV2ProviderTests(unittest.TestCase):
    def identity(self, token="trusted"):
        return TrustedIdentity(
            "org-a", "actor-a", "lskills-api", frozenset({"skills.read", "web.read"}),
            "runtime-binding", roles=frozenset({"researcher"}),
            runtime_profiles=frozenset({"codex-macos"}),
            activated_release_ids=frozenset({"research@1.0.0"}),
        )

    def setUp(self):
        self.families = [
            {"family_id": "research", "display_name": "Research", "description": "Reviewed research.", "subcategories": []},
            {"family_id": "engineering", "display_name": "Engineering", "description": "Reviewed engineering.", "subcategories": []},
            {"family_id": "operations", "display_name": "Operations", "description": "Reviewed operations.", "subcategories": []},
        ]
        self.release = {
            "skill_id": "research", "version": "1.0.0", "family_id": "research",
            "lifecycle_state": "qualified", "qualification": "qualified",
            "roles": ["researcher"], "runtime_profiles": ["codex-macos"],
            "required_capabilities": ["web.read"], "provenance": {
                "source_kind": "native", "publisher": "LiNKskills",
                "repository": "https://github.com/linktrend/LiNKskills", "source_ref": "development",
                "source_commit": "a" * 40, "source_path": "skills/research/SKILL.md",
                "retrieved_at": "2026-08-24T00:00:00Z",
            }, "licence": {"licence_id": "LiNKtrend-proprietary", "attribution_required": False, "review_status": "not_required"},
            "resources": {"entrypoint": {"body": b"exact instructions", "resource_kind": "entrypoint", "media_type": "text/markdown"}},
        }
        self.provider = V2Provider(self.identity, families=self.families, releases=[self.release])
        self.base = {"protocol_version": "2026-07-28", "authorization": "trusted"}

    def call(self, operation, **extra):
        return self.provider.handle(dict(self.base, operation=operation, **extra))

    def test_family_discovery_is_bounded_and_snapshot_paged(self):
        first = self.call("skills_catalog_list", limit=2)
        self.assertEqual([item["family_id"] for item in first["items"]], ["research", "engineering"])
        self.assertTrue(first["has_more"])
        self.assertNotIn("bytes", first["items"][0])
        second = self.call("skills_catalog_list", limit=2, cursor=first["next_cursor"])
        self.assertEqual([item["family_id"] for item in second["items"]], ["operations"])
        self.assertFalse(second["has_more"])
        self.assertEqual(self.call("skills_catalog_list", limit=2, cursor="snapshot:other:0")["error"], "cursor_snapshot_mismatch")

    def test_exact_resource_returns_immutable_bytes_and_digest(self):
        result = self.call("skills_release_resource_get", skill_id="research", version="1.0.0", resource_id="entrypoint")
        self.assertTrue(result["ok"])
        self.assertEqual(result["bytes"], b"exact instructions")
        self.assertEqual(result["content_digest"], result["descriptor"]["content_digest"])
        self.assertTrue(result["immutable"])
        self.assertEqual(self.call("skills_release_resource_get", skill_id="research", version="1.0.0", resource_id="missing")["error"], "not_found")
        self.assertEqual(self.call("skills_release_describe", skill_id="unknown", version="1.0.0")["error"], "not_found")

    def test_role_and_profile_gates_fail_closed(self):
        denied_role = TrustedIdentity("org-a", "actor-a", "lskills-api", frozenset({"skills.read", "web.read"}), "binding", runtime_profiles=frozenset({"codex-macos"}), activated_release_ids=frozenset({"research@1.0.0"}))
        provider = V2Provider(lambda _: denied_role, releases=[self.release], families=self.families)
        self.assertEqual(provider.handle(dict(self.base, operation="skills_release_describe", skill_id="research", version="1.0.0"))["error"], "role_not_authorized")
        profile_denied = dict(self.release, consumer_profile_activation=False)
        provider = V2Provider(self.identity, releases=[profile_denied], families=self.families)
        self.assertEqual(provider.handle(dict(self.base, operation="skills_release_describe", skill_id="research", version="1.0.0"))["error"], "consumer_profile_activation")

    def test_standard_initialize_and_client_verifies_exact_read(self):
        server = ModernSkillsMcpServer(self.provider)
        transport = server.handle_rpc
        client = McpV2Client(transport, authorization="trusted")
        self.assertEqual(client.initialize()["protocolVersion"], "2026-07-28")
        body, digest = client.read_exact("skills://release/research/1.0.0/resource/entrypoint")
        self.assertEqual(body, b"exact instructions")
        self.assertTrue(digest.startswith("sha256:"))
        with self.assertRaises(McpV2Error):
            client.read_exact("skills://release/research/1.0.0/resource/entrypoint", expected_digest="sha256:" + "0" * 64)
