import unittest
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
