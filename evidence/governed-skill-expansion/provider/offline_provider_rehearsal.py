"""Deterministic loopback-only PKT-25 provider rehearsal.

The fake provider is in-process and never opens a socket. The receipt remains
``LOCAL_ONLY`` and explicitly claims no external provider or runtime proof.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from package_receipt import bind_receipt, canonical_json, digest_json, package_identity, sha256_bytes


LOOPBACK_ENDPOINT = "loopback://offline-provider"
PACKAGE_ID = "research/offline-rehearsal"
PACKAGE_VERSION = "0.0.0-rehearsal"
SECRET_KEY_RE = re.compile(r"(token|secret|password|private[_-]?key|dsn|cookie|credential)", re.IGNORECASE)


class ProviderOffline(RuntimeError):
    """Raised when the fake provider is deliberately disconnected."""


def _redact(value: Any) -> Any:
    """Recursively redact values whose keys could contain credentials."""

    if isinstance(value, Mapping):
        return {field_name: "<redacted>" if SECRET_KEY_RE.search(str(field_name)) else _redact(item)
                for field_name, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _event_id(event: Mapping[str, Any]) -> str:
    """Derive a stable event id from the redacted event payload."""

    return sha256_bytes(canonical_json(_redact(event)))


@dataclass
class FakeLoopbackProvider:
    """Minimal in-process provider with exact-release behavior."""

    connected: bool = True
    package_bytes: bytes = b"offline-rehearsal-package\n"
    manifest: dict[str, Any] = field(default_factory=lambda: {"entrypoint": "run", "files": ["package.txt"]})

    def list_catalogue(self) -> list[dict[str, str]]:
        """Return bounded metadata without executing a skill."""

        self._require_connection()
        return [{"package_id": PACKAGE_ID, "version": PACKAGE_VERSION, "state": "available"}]

    def retrieve_exact(self, package_id: str, version: str) -> bytes:
        """Return only the requested immutable rehearsal package."""

        self._require_connection()
        if package_id != PACKAGE_ID or version != PACKAGE_VERSION:
            raise KeyError("exact_release_not_found")
        return self.package_bytes

    def _require_connection(self) -> None:
        if not self.connected:
            raise ProviderOffline("fake_provider_disconnected")


@dataclass
class OfflineEventBuffer:
    """Redacted, idempotent local buffer used while the fake provider is down."""

    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    flushed: set[str] = field(default_factory=set)

    def append(self, event: Mapping[str, Any]) -> str:
        """Store a redacted event once and return its stable id."""

        redacted = _redact(dict(event))
        event_id = _event_id(redacted)
        self.events.setdefault(event_id, {"event_id": event_id, "payload": redacted})
        return event_id

    def flush(self, provider: FakeLoopbackProvider) -> dict[str, int]:
        """Replay each event once; repeated flushes are idempotent."""

        provider._require_connection()
        pending = [event_id for event_id in self.events if event_id not in self.flushed]
        self.flushed.update(pending)
        return {"sent": len(pending), "duplicates_ignored": len(self.events) - len(pending)}


def default_identity() -> dict[str, str]:
    """Read local Git identity without contacting a provider or remote."""

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()

    return {"repository": git("remote", "get-url", "origin").removesuffix(".git"),
            "ref": git("rev-parse", "--abbrev-ref", "HEAD"),
            "commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}")}


def rehearse(identity: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Run the complete local rehearsal and return a source-only receipt."""

    identity = dict(identity or default_identity())
    provider = FakeLoopbackProvider()
    buffer = OfflineEventBuffer()
    bound_identity = package_identity(
        **identity, package_id=PACKAGE_ID, package_version=PACKAGE_VERSION,
        package_bytes=provider.package_bytes, manifest=provider.manifest,
    )
    catalogue = provider.list_catalogue()
    retrieved = provider.retrieve_exact(PACKAGE_ID, PACKAGE_VERSION)
    exact_digest_match = sha256_bytes(retrieved) == bound_identity["package_sha256"]
    provider.connected = False
    offline_event = {"kind": "skills.feedback", "package_id": PACKAGE_ID,
                     "version": PACKAGE_VERSION, "diagnostics": "fixture-only",
                     "credential_probe": "fixture-token-must-not-escape"}
    event_id = buffer.append(offline_event)
    try:
        provider.list_catalogue()
    except ProviderOffline:
        disconnected = True
    else:
        disconnected = False
    provider.connected = True
    first_flush = buffer.flush(provider)
    second_flush = buffer.flush(provider)
    checks = {
        "loopback_endpoint": LOOPBACK_ENDPOINT.startswith("loopback://"),
        "bounded_catalogue": len(catalogue) == 1 and catalogue[0]["package_id"] == PACKAGE_ID,
        "exact_package_digest": exact_digest_match,
        "disconnect_is_fail_closed": disconnected,
        "stable_event_id": event_id == _event_id(offline_event),
        "single_flush": first_flush == {"sent": 1, "duplicates_ignored": 0},
        "duplicate_flush_is_idempotent": second_flush == {"sent": 0, "duplicates_ignored": 1},
        "redacted_buffer": "fixture-token" not in json.dumps(buffer.events, sort_keys=True),
    }
    result = {
        "schema_version": "0.1", "kind": "linkskills.pkt-25.offline-provider-rehearsal",
        "status": "LOCAL_ONLY", "endpoint": LOOPBACK_ENDPOINT,
        "claims": {"provider_live": False, "consumer_configured": False,
                    "stage_proven": False, "vps_proven": False,
                    "e2e_proven": False, "production_proven": False},
        "package": {**bound_identity, "manifest": provider.manifest},
        "rehearsal": {"checks": checks, "all_checks_pass": all(checks.values()), "event_id": event_id},
        "safety": {"network_contacted": False, "real_credentials_used": False,
                    "activation_or_pointer_change": False, "external_evidence": False},
    }
    result["result_sha256"] = digest_json(result)
    return bind_receipt(result, bound_identity, result_digest=result["result_sha256"],
                        checkout_identity=identity, provider_identity=identity)


def main(argv: list[str] | None = None) -> int:
    """Run the rehearsal, optionally writing its local-only receipt."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    receipt = rehearse()
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if receipt["rehearsal"]["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
