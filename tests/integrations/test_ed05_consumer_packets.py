"""ED-05 source-only consumer packet schema, digest, allowlist, and fake-contract tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ed05_fake_contracts import (  # noqa: E402
    FIXTURE_PROVIDER,
    FIXTURE_TOKEN,
    FakePlatform,
    FakeProvider,
    canonical_digest,
    deny_reasons_for,
    ed04_release_index,
    load_json,
    load_pins,
    pin_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION = REPO_ROOT / "configs" / "consumer-activation"
FRAGMENTS = REPO_ROOT / "configs" / "fragments"
DOCS = REPO_ROOT / "docs" / "integrations" / "ed-05"
SCHEMA = ACTIVATION / "ed-05-owner-packet.schema.json"
PACKETS = (
    ACTIVATION / "ed-05-cursor-owner-packet.json",
    ACTIVATION / "ed-05-codex-owner-packet.json",
    ACTIVATION / "ed-05-lisa-openclaw-owner-packet.json",
)
SECRETISH = re.compile(
    r"(BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-)",
    re.I,
)
ALLOWLIST = (
    "git-safeguard@1.1.0",
    "persistent-qa@1.0.0",
    "repository-manager@1.0.0",
    "skill-template@1.2.0",
    "tool-architect@1.0.0",
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return load_json(SCHEMA)


@pytest.fixture(scope="module")
def packets() -> list[dict]:
    return [load_json(path) for path in PACKETS]


def test_three_packets_validate_and_stay_disabled(schema: dict, packets: list[dict]) -> None:
    validator = jsonschema.Draft202012Validator(schema)
    ids = []
    for packet, path in zip(packets, PACKETS, strict=True):
        errors = sorted(validator.iter_errors(packet), key=lambda e: e.json_path)
        assert not errors, f"{path.name}: {[e.message for e in errors]}"
        assert packet["disabledByDefault"] is True
        assert packet["activation"]["enabled"] is False
        assert packet["activation"]["liveApply"] is False
        assert packet["privateEndpoint"]["liveUrl"] is None
        ids.append(packet["packetId"])
    assert ids == ["ed-05-cursor", "ed-05-codex", "ed-05-lisa-openclaw"]


def test_pins_match_ed04_receipt_exactly() -> None:
    pins = pin_index()
    published = ed04_release_index()
    assert tuple(pins) == ALLOWLIST
    for release_id, pin in pins.items():
        row = published[release_id]
        assert pin["bundleDigest"] == row["bundleDigest"]
        assert pin["packageDigest"] == row["packageDigest"]
        assert pin["filesDigest"] == row["filesDigest"]
        assert pin["sourceDigest"] == row["sourceDigest"]
        assert pin["evalDigest"] == row["evalDigest"]
        assert pin["profileDigest"] == row["profileDigest"]
        assert pin["toolDigest"] == row["toolDigest"]
        assert pin["version"] == row["version"]
        assert pin["runtimeProfile"] == "cursor-macos"


def test_each_packet_embeds_the_shared_pin_table(packets: list[dict]) -> None:
    shared = load_pins()["releases"]
    for packet in packets:
        assert packet["allowlist"] == list(ALLOWLIST)
        assert packet["pins"] == shared
        assert packet["pinsRef"].endswith("ed-05-initial-five-pins.json")


def test_expansion_internal_canary_manifests_remain_disabled() -> None:
    paths = sorted(ACTIVATION.glob("*-internal-canary.json"))
    assert len(paths) >= 4
    for path in paths:
        manifest = load_json(path)
        assert manifest["activation"]["enabled"] is False
        assert manifest["live_apply"] is False


def test_fragments_disabled_no_secrets_and_brain_names_separated() -> None:
    cursor = load_json(FRAGMENTS / "ed-05-cursor-skills.mcp.json.fragment")
    openclaw = load_json(FRAGMENTS / "ed-05-openclaw-skills.mcp.json.fragment")
    codex = (FRAGMENTS / "ed-05-codex-skills.config.toml.fragment").read_text(encoding="utf-8")
    assert cursor["mcpServers"]["linkskills-ed05-cursor"]["disabled"] is True
    assert openclaw["disabled"] is True
    assert "enabled = false" in codex
    assert "linkskills_ed05_codex" in codex
    for blob in (json.dumps(cursor), json.dumps(openclaw), codex):
        assert SECRETISH.search(blob) is None
        assert "lbrain-api" not in blob
        assert "lskills-api" in blob
        assert "lskills" in blob
    assert "skills_run_" in json.dumps(openclaw["operations"]["denied"])
    assert "skills_tool_" in json.dumps(openclaw["operations"]["denied"])


def test_docs_and_handoffs_exist_and_forbid_live_apply() -> None:
    for name in (
        "README.md",
        "CURSOR-OWNER-PACKET.md",
        "CODEX-OWNER-PACKET.md",
        "LISA-OPENCLAW-OWNER-PACKET.md",
    ):
        text = (DOCS / name).read_text(encoding="utf-8")
        assert "disabled" in text.lower()
        assert "not live" in text.lower() or "live_apply=false" in text or "not live" in text


def test_fake_platform_mints_skills_and_rejects_brain() -> None:
    platform = FakePlatform()
    ok = platform.mint(
        audience="lskills-api",
        scope="lskills",
        client_kind="skills",
        token_endpoint=FIXTURE_TOKEN,
    )
    assert ok["ok"] is True
    assert ok["handle"].startswith("opaque:")
    assert platform.mint(
        audience="lbrain-api",
        scope="lskills",
        client_kind="skills",
        token_endpoint=FIXTURE_TOKEN,
    )["error"] == "brain_audience_rejected"
    assert platform.mint(
        audience="lskills-api",
        scope="lskills",
        client_kind="brain",
        token_endpoint=FIXTURE_TOKEN,
    )["error"] == "brain_credential_rejected"
    assert platform.mint(
        audience="lskills-api",
        scope="lskills",
        client_kind="skills",
        token_endpoint="https://auth.example.com/token",
    )["error"] == "unknown_token_endpoint"


def test_fake_provider_retrieval_verify_execute_and_use_report() -> None:
    provider = FakeProvider(pins=pin_index())
    handle = FakePlatform().mint(
        audience="lskills-api",
        scope="lskills",
        client_kind="skills",
        token_endpoint=FIXTURE_TOKEN,
    )["handle"]
    pin = pin_index()["git-safeguard@1.1.0"]
    retrieved = provider.retrieve(
        skill_id="git-safeguard",
        version="1.1.0",
        digest=pin["bundleDigest"],
        handle=handle,
    )
    assert retrieved["ok"] is True
    assert retrieved["endpoint"] == FIXTURE_PROVIDER
    assert retrieved["disabledPacket"] is True
    assert provider.verify(
        "git-safeguard@1.1.0", pin["bundleDigest"], pin["packageDigest"]
    )["ok"] is True
    executed = provider.execute_locally(retrieved)
    assert executed["ok"] is True
    assert executed["providerExecuted"] is False
    report = {
        "schema_version": "0.2",
        "report_kind": "completed_use",
        "report_id": "opaque:report:ed05-10",
        "occurred_at": "2026-09-12T00:00:00Z",
        "skill_id": "git-safeguard",
        "skill_release_ref": "opaque:release:git-safeguard:1.1.0",
        "consumer_class": "cursor",
        "actor_ref": "opaque:actor:cursor-fixture",
        "runtime_profile_ref": "opaque:runtime:cursor-macos",
        "outcome": "use_succeeded",
        "opaque_refs": ["opaque:packet:ed-05-cursor"],
        "idempotency_source": "server",
        "server_idempotency_key": "sha256:" + ("ab" * 32),
        "score": 10,
    }
    use_schema = load_json(REPO_ROOT / "packages" / "contracts" / "schemas" / "use-report-v0.2.json")
    jsonschema.Draft202012Validator(use_schema).validate(report)
    assert provider.submit_use_report(report)["ok"] is True
    dirty = dict(report)
    dirty["opaque_refs"] = list(report["opaque_refs"]) + ["opaque:note:transcript"]
    assert provider.submit_use_report(dirty)["error"] == "forbidden_payload"


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"skill_id": "git-safeguards", "version": "1.1.0"}, "similar_name_denied"),
        ({"skill_id": "git-safeguard", "version": "0.0.1"}, "release_not_selectable"),
        ({"skill_id": "audit-protocol", "version": "1.0.0"}, "release_not_selectable"),
        ({"skill_id": "git-safeguard", "version": "1.1.0", "digest": "sha256:" + ("00" * 32)}, "digest_mismatch"),
        ({"skill_id": "git-safeguard", "version": "1.1.0", "use_stale": True}, "unapproved_fallback_denied"),
        ({"skill_id": "git-safeguard", "version": "1.1.0", "use_latest": True}, "unapproved_fallback_denied"),
        ({"skill_id": "git-safeguard", "version": "1.1.0", "fallback": "cursor-native-git"}, "native_substitute_denied"),
    ],
)
def test_deny_stale_similar_native_and_unknown(kwargs: dict, error: str) -> None:
    provider = FakeProvider(pins=pin_index())
    handle = FakePlatform().mint(
        audience="lskills-api",
        scope="lskills",
        client_kind="skills",
        token_endpoint=FIXTURE_TOKEN,
    )["handle"]
    pin = pin_index()["git-safeguard@1.1.0"]
    result = provider.retrieve(
        digest=kwargs.pop("digest", pin["bundleDigest"]),
        handle=handle,
        **kwargs,
    )
    assert result["ok"] is False
    assert result["error"] == error


def test_legacy_execution_and_rollback(packets: list[dict]) -> None:
    provider = FakeProvider(pins=pin_index())
    assert provider.deny_legacy("skills_run_start")["error"] == "legacy_execution_disabled"
    assert provider.deny_legacy("skills_tool_invoke")["error"] == "legacy_execution_disabled"
    assert provider.deny_legacy("skills_release_verify")["ok"] is True
    rolled = provider.rollback(packets[0])
    assert rolled["ok"] is True
    assert rolled["providerPinsUnchanged"] is True
    enabled = json.loads(json.dumps(packets[0]))
    enabled["activation"]["enabled"] = True
    assert provider.rollback(enabled)["error"] == "packet_still_enabled"


def test_deny_reason_helper_covers_allowlist() -> None:
    assert "similar_name" in deny_reasons_for({"skillId": "git-safeguards", "version": "1.1.0"})
    assert "not_allowlisted" in deny_reasons_for({"skillId": "canary-echo", "version": "1.0.0"})
    pin = pin_index()["tool-architect@1.0.0"]
    assert deny_reasons_for(
        {
            "skillId": "tool-architect",
            "version": "1.0.0",
            "digest": pin["bundleDigest"],
        }
    ) == ["denied"]


def test_packet_and_pin_digests_are_stable() -> None:
    pins = load_pins()
    assert canonical_digest(pins).startswith("sha256:")
    for path in PACKETS:
        digest = canonical_digest(load_json(path))
        assert len(digest) == 71


def test_no_secret_values_in_owned_ed05_files() -> None:
    owned = list(ACTIVATION.glob("ed-05-*")) + list(FRAGMENTS.glob("ed-05-*")) + list(DOCS.glob("*"))
    for path in owned:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert SECRETISH.search(text) is None
        assert "BEGIN RSA" not in text
