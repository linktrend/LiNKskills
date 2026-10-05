"""End-to-end URI round trips for exact MCP resource reads."""

from __future__ import annotations

import base64
import hashlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from linkskills_client.mcp_v2 import McpV2Client, McpV2Error
from linkskills_core.mcp_v2 import ExactResource, release_resource_uri
from linkskills_core.provider_v2 import PROTOCOL_VERSION, TrustedIdentity, V2Provider
from linkskills_gateway.production_v2 import ProductionV2Provider, manifest_digest
from linkskills_mcp.v2_provider import ModernSkillsMcpServer


def _sha(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _identity(
    token: str,
    *,
    roles: frozenset[str] = frozenset({"reviewer"}),
    binding: str = "binding-a",
) -> TrustedIdentity:
    if token != "trusted":
        raise ValueError("bad token")
    return TrustedIdentity(
        "org-a",
        "actor-a",
        "lskills-api",
        frozenset({"skills.read"}),
        binding,
        roles=roles,
        runtime_profiles=frozenset({"cursor-macos"}),
        activated_release_ids=frozenset({"research@1.0.0"}),
    )


def _uri_release(resources: dict[str, bytes], *, roles: list[str] | None = None) -> dict:
    return {
        "skill_id": "research",
        "version": "1.0.0",
        "family_id": "research",
        "lifecycle_state": "qualified",
        "qualification": "qualified",
        "roles": roles or ["reviewer"],
        "runtime_profiles": ["cursor-macos"],
        "required_capabilities": ["skills.read"],
        "resources": {
            resource_id: {
                "body": body,
                "resource_kind": "reference",
                "media_type": "application/octet-stream",
            }
            for resource_id, body in resources.items()
        },
    }


def _read_rpc(server: ModernSkillsMcpServer, uri: str, **extra) -> dict:
    return server.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "resources/read",
            "params": {"uri": uri, **extra, "_meta": {"authorization": "trusted"}},
        }
    )["result"]


class _MetadataStore:
    """Small fake store exercising the real production metadata path."""

    def __init__(self, resources: dict[str, bytes]) -> None:
        descriptors = {}
        for resource_id, body in resources.items():
            descriptors[resource_id] = {
                "content_b64": base64.b64encode(body).decode("ascii"),
                "content_digest": _sha(body),
                "byte_size": len(body),
                "media_type": "text/markdown",
                "resource_kind": "reference",
            }
        self.row = {
            "release_id": "research@1.0.0",
            "manifest": {
                "skill_id": "research",
                "version": "1.0.0",
                "qualification": "qualified",
                "lifecycle_state": "qualified",
                "family_id": "research",
                "runtime_profiles": ["cursor-macos"],
                "roles": ["reviewer"],
                "required_capabilities": ["skills.read"],
                "resources": descriptors,
            },
            "lifecycle": "qualified",
        }
        self.row["manifest_sha256"] = manifest_digest(self.row["manifest"])
        self.binding = {"runtime_profile": "cursor-macos", "release_ids": ["research@1.0.0"]}
        self.metadata_fetches = []

    def snapshot_metadata(self, claims):
        manifest = self.row["manifest"]
        return (
            [
                {
                    **{key: value for key, value in manifest.items() if key != "resources"},
                    "release_id": self.row["release_id"],
                    "lifecycle_state": self.row["lifecycle"],
                }
            ],
            self.binding,
        )

    def fetch_release_metadata(self, claims, release_id):
        self.metadata_fetches.append(release_id)
        if release_id != self.row["release_id"]:
            raise ValueError("not_found")
        return {"row": self.row, "binding": self.binding}

    def fetch_release(self, claims, release_id, resource_ids=None):
        if release_id != self.row["release_id"]:
            raise ValueError("not_found")
        return {"row": self.row, "binding": self.binding}


def _production_server(resources: dict[str, bytes]):
    auth = Mock()
    auth.verify.return_value = SimpleNamespace(
        org_id="org-a",
        actor_id="actor-a",
        runtime_binding_id="binding-a",
        scopes={"skills:read"},
        permitted_operations={"read"},
        roles={"reviewer"},
    )
    provider = ProductionV2Provider(auth, _MetadataStore(resources))
    return ModernSkillsMcpServer(provider)


def test_in_memory_descriptor_uris_round_trip_opaque_resource_ids() -> None:
    resources = {
        "references/schemas.json": b'{"schema": "nested"}',
        "references/a b#c?d%.md": b"space hash query percent",
        "references/会計/模組.md": "繁體中文內容".encode("utf-8"),
        "references/literal%2Ftoken.md": b"literal percent-two-f",
        "references/literal/token.md": b"actual nested slash",
    }
    provider = V2Provider(_identity, releases=[_uri_release(resources)])
    listed = provider.handle(
        {
            "protocol_version": PROTOCOL_VERSION,
            "authorization": "trusted",
            "operation": "skills_release_resources_list",
            "skill_id": "research",
            "version": "1.0.0",
            "limit": 20,
        }
    )
    assert listed["ok"] is True
    descriptors = {row["resource_id"]: row for row in listed["items"]}
    assert set(descriptors) == set(resources)

    server = ModernSkillsMcpServer(provider)
    client = McpV2Client(server.handle_rpc, authorization="trusted")
    client.initialize()
    for resource_id, expected_body in resources.items():
        descriptor = descriptors[resource_id]
        uri = descriptor["resource_uri"]
        assert descriptor["resource_uri"] == release_resource_uri("research", "1.0.0", resource_id)
        result = _read_rpc(server, uri)
        assert result.get("isError") is not True
        assert result["structuredContent"]["resource_id"] == resource_id
        assert result["structuredContent"]["content_digest"] == descriptor["content_digest"]
        body, digest = client.read_exact(uri, expected_digest=descriptor["content_digest"])
        assert body == expected_body
        assert digest == _sha(expected_body)

    literal_uri = descriptors["references/literal%2Ftoken.md"]["resource_uri"]
    assert "%252F" in literal_uri
    literal, _ = client.read_exact(literal_uri)
    assert literal == b"literal percent-two-f"
    assert literal != resources["references/literal/token.md"]


def test_production_metadata_emitter_uri_reads_exact_fake_store_bytes() -> None:
    resources = {
        "references/政策/one file#readme?.md": b"production metadata body",
        "references/nested/schemas.json": b'{"answer": 42}',
    }
    server = _production_server(resources)
    client = McpV2Client(server.handle_rpc, authorization="trusted")
    client.initialize()
    listed = server.provider.handle(
        {
            "operation": "skills_release_resources_list",
            "protocol_version": PROTOCOL_VERSION,
            "authorization": "trusted",
            "skill_id": "research",
            "version": "1.0.0",
            "limit": 20,
        }
    )
    assert listed["ok"] is True
    assert server.provider.store.metadata_fetches == ["research@1.0.0"]
    descriptors = {row["resource_id"]: row for row in listed["items"]}
    assert set(descriptors) == set(resources)
    for resource_id, expected_body in resources.items():
        descriptor = descriptors[resource_id]
        assert descriptor["resource_uri"] == release_resource_uri("research", "1.0.0", resource_id)
        body, digest = client.read_exact(
            descriptor["resource_uri"], expected_digest=descriptor["content_digest"]
        )
        assert body == expected_body
        assert digest == _sha(expected_body)


def test_bad_uri_and_unknown_resource_fail_without_fallback_bytes() -> None:
    provider = V2Provider(
        _identity,
        releases=[_uri_release({"entrypoint": b"entrypoint bytes", "references/known.md": b"known bytes"})],
    )
    server = ModernSkillsMcpServer(provider)
    bad_uris = [
        "skills://release/research/1.0.0/resource/references/bad%",
        "skills://release/research/1.0.0/resource/references/bad%2",
        "skills://release/research/1.0.0/resource/references/bad%FF",
        "skills://release/research/1.0.0/resource/references/bad%ED%A0%80",
        "skills://release/research/1.0.0/resource/references/known.md#fragment",
        "skills://release/research/1.0.0/resource/references/raw\x01control.md",
        "skills://release/research/1.0.0/resource/references/raw space.md",
        "skills://release/research/1.0.0/resource/references/raw\ud800.md",
        "skills://release/research/1.0.0/resource/references/raw%20\ud800.md",
    ]
    for uri in bad_uris:
        result = _read_rpc(server, uri)
        assert result["isError"] is True, repr(uri)
        assert result["contents"] == [], repr(uri)
        assert result["structuredContent"]["error"] == "unsupported_operation"

    unknown = _read_rpc(server, release_resource_uri("research", "1.0.0", "references/unknown.md"))
    assert unknown["isError"] is True
    assert unknown["contents"] == []
    assert unknown["structuredContent"]["error"] == "not_found"

    wrong_digest = _read_rpc(
        server,
        release_resource_uri("research", "1.0.0", "references/known.md"),
        expected_digest=_sha(b"not the resource"),
    )
    assert wrong_digest["isError"] is True
    assert wrong_digest["contents"] == []
    assert wrong_digest["structuredContent"]["error"] == "validation_failed"


def test_uri_reads_preserve_auth_role_binding_and_identity_gates() -> None:
    resource = "references/secure/nested.md"
    release = _uri_release({resource: b"protected bytes"}, roles=["reviewer"])
    uri = ExactResource(resource, b"protected bytes", resource_kind="reference").descriptor(
        "research", "1.0.0"
    )["resource_uri"]

    unauthenticated = ModernSkillsMcpServer(V2Provider(_identity, releases=[release])).handle_rpc(
        {"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": uri}}
    )["result"]
    assert unauthenticated["isError"] is True
    assert unauthenticated["contents"] == []
    assert unauthenticated["structuredContent"]["error"] == "auth_required"

    wrong_role_provider = V2Provider(
        lambda token: _identity(token, roles=frozenset({"reader"})), releases=[release]
    )
    wrong_role = _read_rpc(ModernSkillsMcpServer(wrong_role_provider), uri)
    assert wrong_role["isError"] is True
    assert wrong_role["contents"] == []
    assert wrong_role["structuredContent"]["error"] == "forbidden"

    missing_binding_provider = V2Provider(
        lambda token: _identity(token, binding=""), releases=[release]
    )
    missing_binding = _read_rpc(ModernSkillsMcpServer(missing_binding_provider), uri)
    assert missing_binding["isError"] is True
    assert missing_binding["contents"] == []
    assert missing_binding["structuredContent"]["error"] == "auth_invalid"

    provider = V2Provider(_identity, releases=[release])
    spoofed = _read_rpc(
        ModernSkillsMcpServer(provider),
        uri,
        operation="skills_catalog_list",
        authorization="forged",
        skill_id="attacker",
        version="9.9.9",
        resource_id="entrypoint",
        org_id="org-attacker",
        actor_id="actor-attacker",
        binding="binding-attacker",
        capabilities=["admin"],
        roles=["administrator"],
    )
    assert spoofed.get("isError") is not True
    assert spoofed["structuredContent"]["resource_id"] == resource
    assert base64.b64decode(spoofed["contents"][0]["blob"], validate=True) == b"protected bytes"


def test_client_digest_mismatch_rejects_exact_mcp_payload() -> None:
    provider = V2Provider(_identity, releases=[_uri_release({"references/digest.md": b"exact bytes"})])
    client = McpV2Client(ModernSkillsMcpServer(provider).handle_rpc, authorization="trusted")
    with pytest.raises(McpV2Error, match="integrity_mismatch"):
        client.read_exact(
            release_resource_uri("research", "1.0.0", "references/digest.md"),
            expected_digest=_sha(b"different"),
        )
