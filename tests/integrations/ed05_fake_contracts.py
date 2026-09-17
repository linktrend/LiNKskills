"""Fake Platform and provider-v2 contracts for ED-05 source-only packets.

No live HTTP, credentials, or consumer-repo mutation. Tokens are opaque
fixture strings, never JWTs or secret material.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
PINS_PATH = REPO_ROOT / "configs" / "consumer-activation" / "ed-05-initial-five-pins.json"
ED04_RECEIPT = (
    REPO_ROOT / "evidence" / "end-to-end-delivery" / "ed-04" / "source-publication-receipt.json"
)
SKILLS_AUDIENCE = "lskills-api"
SKILLS_SCOPE = "lskills"
BRAIN_AUDIENCE = "lbrain-api"
FIXTURE_PROVIDER = "https://skills.test.linktrend.invalid/provider-v2"
FIXTURE_TOKEN = "https://auth.test.linkplatform.invalid/oauth/token"
DIGEST_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
SIMILAR_NAMES = {
    "git-safeguard": ("git-safeguards", "git_safeguard", "git-guard", "gitsafeguard"),
    "persistent-qa": ("persistent-q-a", "persistentqa", "qa-persistent"),
    "repository-manager": ("repo-manager", "repository_manager", "repo-mgmt"),
    "skill-template": ("skills-template", "skill_template", "template-skill"),
    "tool-architect": ("tools-architect", "tool_architect", "architect-tool"),
}
NATIVE_SUBSTITUTES = frozenset(
    {"cursor-native-git", "codex-builtin-review", "openclaw-native-planner"}
)


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pins() -> dict[str, Any]:
    return load_json(PINS_PATH)


def pin_index() -> dict[str, dict[str, Any]]:
    return {row["releaseId"]: row for row in load_pins()["releases"]}


def ed04_release_index() -> dict[str, dict[str, Any]]:
    receipt = load_json(ED04_RECEIPT)
    return {row["releaseId"]: row for row in receipt["releases"]}


@dataclass
class FakePlatform:
    """Platform claim/token mint fixture. Skills and Brain stay separate."""

    minted: list[dict[str, Any]] = field(default_factory=list)

    def mint(
        self,
        *,
        audience: str,
        scope: str,
        client_kind: str,
        token_endpoint: str,
    ) -> dict[str, Any]:
        if token_endpoint != FIXTURE_TOKEN:
            return {"ok": False, "error": "unknown_token_endpoint"}
        if client_kind == "brain":
            return {"ok": False, "error": "brain_credential_rejected"}
        if audience == BRAIN_AUDIENCE:
            return {"ok": False, "error": "brain_audience_rejected"}
        if audience != SKILLS_AUDIENCE or scope != SKILLS_SCOPE:
            return {"ok": False, "error": "auth_invalid"}
        if client_kind != "skills":
            return {"ok": False, "error": "auth_invalid"}
        handle = "opaque:ed05-fixture-handle:skills"
        record = {
            "ok": True,
            "handle": handle,
            "audience": audience,
            "scope": scope,
            "handle_type": "fixture_opaque",
            "live": False,
        }
        self.minted.append(record)
        return record

    def verify_bearer(self, handle: str) -> dict[str, Any]:
        if handle != "opaque:ed05-fixture-handle:skills":
            return {"ok": False, "error": "auth_invalid"}
        return {"ok": True, "audience": SKILLS_AUDIENCE, "scope": SKILLS_SCOPE}


@dataclass
class FakeProvider:
    """Exact-release provider fixture bound to ED-05 pins."""

    pins: dict[str, dict[str, Any]]
    disabled: bool = True
    reports: list[dict[str, Any]] = field(default_factory=list)

    def retrieve(
        self,
        *,
        skill_id: str,
        version: str,
        digest: str,
        handle: str,
        fallback: str | None = None,
        use_stale: bool = False,
        use_latest: bool = False,
    ) -> dict[str, Any]:
        auth = FakePlatform().verify_bearer(handle)
        if not auth["ok"]:
            return {"ok": False, "error": auth["error"]}
        if fallback in NATIVE_SUBSTITUTES:
            return {"ok": False, "error": "native_substitute_denied"}
        if use_stale or use_latest:
            return {"ok": False, "error": "unapproved_fallback_denied"}
        similar = {alias for group in SIMILAR_NAMES.values() for alias in group}
        if skill_id in similar:
            return {"ok": False, "error": "similar_name_denied"}
        release_id = f"{skill_id}@{version}"
        pin = self.pins.get(release_id)
        if pin is None:
            return {"ok": False, "error": "release_not_selectable"}
        if not DIGEST_RE.fullmatch(digest) or digest not in {
            pin["bundleDigest"],
            pin["packageDigest"],
        }:
            return {"ok": False, "error": "digest_mismatch"}
        if fallback:
            return {"ok": False, "error": "unapproved_fallback_denied"}
        return {
            "ok": True,
            "releaseId": release_id,
            "bundleDigest": pin["bundleDigest"],
            "packageDigest": pin["packageDigest"],
            "endpoint": FIXTURE_PROVIDER,
            "executed": False,
            "disabledPacket": self.disabled,
        }

    def verify(self, release_id: str, bundle_digest: str, package_digest: str) -> dict[str, Any]:
        pin = self.pins.get(release_id)
        if pin is None:
            return {"ok": False, "error": "release_not_selectable"}
        if pin["bundleDigest"] != bundle_digest or pin["packageDigest"] != package_digest:
            return {"ok": False, "error": "digest_mismatch"}
        return {"ok": True, "releaseId": release_id}

    def execute_locally(self, retrieval: Mapping[str, Any]) -> dict[str, Any]:
        if not retrieval.get("ok"):
            return {"ok": False, "error": "cannot_execute_denied_retrieval"}
        if retrieval.get("executed"):
            return {"ok": False, "error": "provider_must_not_execute"}
        return {
            "ok": True,
            "mode": "consumer-local",
            "releaseId": retrieval["releaseId"],
            "providerExecuted": False,
        }

    def deny_legacy(self, operation: str) -> dict[str, Any]:
        if operation.startswith("skills_run_") or operation.startswith("skills_tool_"):
            return {"ok": False, "error": "legacy_execution_disabled"}
        return {"ok": True, "operation": operation}

    def submit_use_report(self, report: Mapping[str, Any]) -> dict[str, Any]:
        forbidden = ("transcript", "conversation", "password")
        blob = json.dumps(report).lower()
        if any(key in blob for key in forbidden):
            return {"ok": False, "error": "forbidden_payload"}
        if report.get("schema_version") != "0.2":
            return {"ok": False, "error": "validation_failed"}
        if report.get("score") == 10 and "issue" in report:
            return {"ok": False, "error": "validation_failed"}
        self.reports.append(dict(report))
        return {"ok": True, "accepted": True, "live": False}

    def rollback(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        if packet.get("activation", {}).get("enabled") is True:
            return {"ok": False, "error": "packet_still_enabled"}
        pins_after = pin_index()
        return {
            "ok": True,
            "providerPinsUnchanged": pins_after == self.pins,
            "localBootstrap": ["agentsetup@1.3.0", "agentcomply@1.3.0"],
            "live": False,
        }


def deny_reasons_for(request: Mapping[str, Any]) -> list[str]:
    """Map a consumer request onto ED-04/ED-05 deny classes."""

    reasons: list[str] = []
    skill_id = str(request.get("skillId") or "")
    version = str(request.get("version") or "")
    digest = str(request.get("digest") or "")
    release_id = f"{skill_id}@{version}"
    pins = pin_index()
    if request.get("native"):
        reasons.append("native_substitute")
    if request.get("stale") or request.get("latest"):
        reasons.append("unapproved_fallback")
    if skill_id in {alias for group in SIMILAR_NAMES.values() for alias in group}:
        reasons.append("similar_name")
    if release_id not in pins:
        reasons.append("not_allowlisted")
    elif digest and digest not in {pins[release_id]["bundleDigest"], pins[release_id]["packageDigest"]}:
        reasons.append("digest_mismatch")
    return reasons or ["denied"]
