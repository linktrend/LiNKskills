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
        self.assertEqual(self.call("skills_release_describe")["error"], "validation_failed")
        missing = self.call("skills_release_describe", skill_id="safe", version="1.0.0", cursor=catalog["cursor"])
        self.assertEqual(missing["error"], "catalog_unavailable")
    def test_cursor_protocol_legacy_and_bounds_fail_closed(self):
        for extra, expected in (({"cursor":"bad"},"validation_failed"),({"cursor":"snapshot:wrong:0"},"validation_failed"),({"limit":101},"validation_failed"),({"session_id":"x"},"contract_incompatible"),({"protocol_version":"2024-11-05"},"contract_incompatible")):
            self.assertEqual(self.p.handle(dict(self.base, operation="skills_catalog_list", **extra))["error"], expected)
        self.assertEqual(self.call("skills_run_start")["error"], "legacy_execution_disabled")
        self.assertEqual(self.call("skills_tool_invoke")["error"], "legacy_execution_disabled")
        rpc = ModernSkillsMcpServer(self.p)
        denied = rpc.handle_rpc(
            {"id": 9, "method": "tools/call", "params": {"name": "skills_tool_invoke", "authorization": "trusted"}}
        )
        self.assertTrue(denied["result"]["isError"])
        self.assertEqual(denied["result"]["structuredContent"]["error"], "legacy_execution_disabled")
    def test_modern_rpc_is_sessionless(self):
        server = ModernSkillsMcpServer(self.p)
        omitted = server.handle_rpc({"id":1,"method":"initialize"})
        self.assertEqual(omitted["result"]["error"], "contract_incompatible")
        injected = server.handle_rpc({"id":1,"method":"initialize","params":{"protocol_version":"2026-07-28"}})
        self.assertEqual(injected["result"]["error"], "contract_incompatible")
        negotiated = server.handle_rpc({"id":1,"method":"initialize","params":{"protocolVersion":"2026-07-28"}})
        self.assertEqual(negotiated["result"]["protocolVersion"], "2026-07-28")
        listed = server.handle_rpc({"id":2,"method":"resources/list","params":{"_meta":{"authorization":"trusted"}}})
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
        self.assertEqual(self.call("skills_catalog_list", limit=2, cursor="snapshot:other:0")["error"], "validation_failed")

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
        self.assertEqual(provider.handle(dict(self.base, operation="skills_release_describe", skill_id="research", version="1.0.0"))["error"], "forbidden")
        profile_denied = dict(self.release, consumer_profile_activation=False)
        provider = V2Provider(self.identity, releases=[profile_denied], families=self.families)
        self.assertEqual(provider.handle(dict(self.base, operation="skills_release_describe", skill_id="research", version="1.0.0"))["error"], "forbidden")

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

    def test_empty_registry_exact_ops_fail_closed(self) -> None:
        empty = V2Provider(self.identity)
        for operation, extra in (
            ("skills_release_describe", {"skill_id": "research", "version": "1.0.0"}),
            ("skills_qualification_get", {"skill_id": "research", "version": "1.0.0"}),
            ("skills_release_resource_get", {"skill_id": "research", "version": "1.0.0", "resource_id": "entrypoint"}),
            ("skills_release_content_get", {"skill_id": "research", "version": "1.0.0", "content_id": "blob"}),
            ("skills_release_package_get", {"skill_id": "research", "version": "1.0.0"}),
            ("skills_release_verify", {"skill_id": "research", "version": "1.0.0"}),
        ):
            result = empty.handle(dict(self.base, operation=operation, **extra))
            self.assertEqual(result["error"], "catalog_unavailable", msg=operation)
            self.assertNotIn("bytes", result)

    def test_mcp_receipts_are_tenant_bound_and_write_requires_report_scope(self) -> None:
        from linkskills_core.provider_v2 import InMemoryProviderStore

        store = InMemoryProviderStore()

        def verify(token: str):
            if token == "org-a":
                return TrustedIdentity(
                    "org-a", "actor-a", "lskills-api",
                    frozenset({"skills.read", "skills.feedback"}), "binding",
                )
            if token == "org-b":
                return TrustedIdentity(
                    "org-b", "actor-b", "lskills-api",
                    frozenset({"skills.read", "skills.feedback"}), "binding",
                )
            if token == "actor-c":
                return TrustedIdentity(
                    "org-a", "actor-c", "lskills-api",
                    frozenset({"skills.read", "skills.feedback"}), "binding",
                )
            if token == "reader":
                return TrustedIdentity(
                    "org-a", "actor-a", "lskills-api", frozenset({"skills.read"}), "binding",
                )
            raise ValueError("bad")

        provider = V2Provider(verify, releases=[self.release], families=self.families, store=store)
        server = ModernSkillsMcpServer(provider)
        report = {
            "schema_version": "0.2",
            "report_kind": "completed_use",
            "report_id": "opaque:report:shared",
            "occurred_at": "2026-08-13T00:00:00Z",
            "skill_id": "research",
            "skill_release_ref": "opaque:release:research:1.0.0",
            "consumer_class": "codex",
            "actor_ref": "opaque:actor:a",
            "runtime_profile_ref": "opaque:runtime:codex",
            "outcome": "use_succeeded",
            "opaque_refs": ["opaque:program:run-1"],
            "idempotency_source": "server",
            "score": 10,
        }

        def call(token, name, arguments):
            return server.handle_rpc(
                {
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments,
                        "_meta": {"authorization": token},
                    },
                }
            )["result"]["structuredContent"]

        first = call("org-a", "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-a"})
        self.assertTrue(first["ok"])
        self.assertFalse(first["replay"])
        cross_org = call("org-b", "skills_use_report_status_get", {"report_id": "opaque:report:shared"})
        self.assertEqual(cross_org["error"], "not_found")
        cross_actor = call("actor-c", "skills_use_report_status_get", {"report_id": "opaque:report:shared"})
        self.assertEqual(cross_actor["error"], "not_found")
        collision = call("org-b", "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-b"})
        self.assertTrue(collision["ok"])
        self.assertFalse(collision["replay"])
        own = call("org-a", "skills_use_report_status_get", {"report_id": "opaque:report:shared"})
        self.assertEqual(own["status"], "accepted")
        replay = call("org-a", "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-a"})
        self.assertTrue(replay["replay"])
        denied = call("reader", "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-read"})
        self.assertEqual(denied["error"], "forbidden")
        reader_status = call("reader", "skills_use_report_status_get", {"report_id": "opaque:report:shared"})
        self.assertEqual(reader_status["status"], "accepted")

        injected = server.handle_rpc(
            {
                "id": 99,
                "method": "resources/read",
                "params": {
                    "uri": "skills://catalog",
                    "operation": "skills_use_report_submit",
                    "report": report,
                    "client_idempotency_key": "k-inject",
                    "_meta": {"authorization": "org-a"},
                },
            }
        )
        injected_body = injected["result"]["structuredContent"]
        self.assertTrue(injected_body.get("ok"))
        self.assertEqual(injected_body.get("operation"), "skills_catalog_list")
        self.assertNotIn("receipt_id", injected_body)
        unmapped = server.handle_rpc(
            {
                "id": 100,
                "method": "resources/read",
                "params": {
                    "uri": "skills://tool/skills_use_report_submit",
                    "operation": "skills_use_report_submit",
                    "arguments": {"report": report},
                    "_meta": {"authorization": "org-a"},
                },
            }
        )
        self.assertTrue(unmapped["result"]["isError"])
        self.assertEqual(unmapped["result"]["structuredContent"]["error"], "unsupported_operation")
        forged = call(
            "org-a",
            "skills_use_report_status_get",
            {
                "report_id": "opaque:report:shared",
                "authorization": "org-b",
                "org_id": "org-b",
                "actor_id": "actor-b",
            },
        )
        self.assertEqual(forged["status"], "accepted")
        exclusive = call(
            "org-a",
            "skills_use_report_submit",
            {"report": dict(report, report_id="opaque:report:a-only"), "client_idempotency_key": "k-a-only"},
        )
        self.assertTrue(exclusive["ok"])
        stolen = call(
            "org-b",
            "skills_use_report_status_get",
            {
                "report_id": "opaque:report:a-only",
                "authorization": "org-a",
                "org_id": "org-a",
                "actor_id": "actor-a",
            },
        )
        self.assertEqual(stolen["error"], "not_found")
        created = call(
            "org-b",
            "skills_use_report_submit",
            {
                "report": dict(report, report_id="opaque:report:forged"),
                "client_idempotency_key": "k-forge",
                "authorization": "org-a",
                "org_id": "org-a",
                "actor_id": "actor-a",
            },
        )
        self.assertTrue(created["ok"])
        owner_sees_forged = call("org-a", "skills_use_report_status_get", {"report_id": "opaque:report:forged"})
        self.assertEqual(owner_sees_forged["error"], "not_found")


class SkillsRunScopeParityTests(unittest.TestCase):
    def test_skills_run_alias_maps_write_feedback_without_legacy_execution(self) -> None:
        from linkskills_gateway.auth import ActorClaims
        from linkskills_gateway.v2_http import identity_from_claims as http_identity_from_claims
        from linkskills_mcp.v2_stdio import identity_from_claims as mcp_identity_from_claims

        claims = ActorClaims(
            actor_id="actor-run",
            actor_kind="service",
            org_id="org-run",
            scopes=frozenset({"skills:run"}),
        )
        expected = frozenset({"skills.read", "skills.write", "skills.feedback"})
        http_identity = http_identity_from_claims(claims)
        mcp_identity = mcp_identity_from_claims(claims)
        self.assertEqual(http_identity.capabilities, expected)
        self.assertEqual(mcp_identity.capabilities, expected)
        self.assertEqual(http_identity.capabilities, mcp_identity.capabilities)

        def verify(token):
            if token != "trusted":
                raise ValueError("bad token")
            return mcp_identity

        provider = V2Provider(verify)
        base = {"protocol_version": "2026-07-28", "authorization": "trusted"}
        self.assertEqual(provider.handle(dict(base, operation="skills_run_start"))["error"], "legacy_execution_disabled")
        self.assertEqual(provider.handle(dict(base, operation="skills_tool_invoke"))["error"], "legacy_execution_disabled")
