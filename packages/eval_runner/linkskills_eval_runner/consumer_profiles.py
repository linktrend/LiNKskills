"""Confined consumer-profile drivers for ED-03 qualification.

These drivers execute on digest-pinned sealed Linux. They represent the
declared consumer capability profile (for the initial five:
``cursor-macos``). They are not Cursor/Codex/Lisa GUI actors and they
never mint a ``usable`` classification from a missing owner receipt,
fixture, or prompt.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from linkskills_core.hashing import sha256_hex_text, sha256_prefixed

SCHEMA_VERSION = 1
DRIVER_KIND = "confined_linux_consumer_profile"
DRIVER_VERSION = "ed03-1.0.0"

# Frozen initial combinations use cursor-macos. Codex/Lisa drivers exist so
# missing XP owner receipts can be named exactly when those profiles appear.
CURSOR_MACOS = "cursor-macos"
CODEX_LINUX = "codex-linux"
LISA_OPENCLAW = "lisa-openclaw"

KNOWN_PROFILES = (CURSOR_MACOS, CODEX_LINUX, LISA_OPENCLAW)

# Exact missing-owner identities. Do not invent GSM project IDs or secret values.
ISSUER_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"
ISSUER_AUTHORITY_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_AUTHORITY"
SEALED_IMAGE_ENV = "LINKSKILLS_SEALED_CERT_IMAGE"

OWNER_RECEIPT_SPECS: dict[str, dict[str, str]] = {
    CURSOR_MACOS: {
        "requiredKind": "xp-02-cursor-owner-live-receipt",
        "owner": "XP-02 Cursor consumer owner",
        "observedSourceOnlyReceipt": (
            "evidence/end-to-end-delivery/ed-05/source-consumer-packet-receipt.json"
        ),
    },
    CODEX_LINUX: {
        "requiredKind": "xp-03-codex-owner-live-receipt",
        "owner": "XP-03 Codex consumer owner",
        "observedSourceOnlyReceipt": (
            "evidence/end-to-end-delivery/ed-05/source-consumer-packet-receipt.json"
        ),
    },
    LISA_OPENCLAW: {
        "requiredKind": "xp-04-lisa-openclaw-owner-live-receipt",
        "owner": "XP-04 Lisa/OpenClaw consumer owner",
        "observedSourceOnlyReceipt": (
            "evidence/end-to-end-delivery/ed-05/source-consumer-packet-receipt.json"
        ),
    },
}


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    return sha256_prefixed(
        sha256_hex_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    )


def runtime_digest() -> str:
    """Bind the worker interpreter/OS without claiming a sealed evaluator image."""
    return _digest_mapping(
        {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "system": platform.system(),
            "machine": platform.machine(),
            "release": platform.release(),
            "platform": platform.platform(),
        }
    )


def adapter_digest(*, profile_id: str) -> str:
    return _digest_mapping(
        {
            "driver_kind": DRIVER_KIND,
            "driver_version": DRIVER_VERSION,
            "profile_id": profile_id,
        }
    )


def inspect_owner_receipt(root: Path, profile_id: str) -> dict[str, Any]:
    """Return the exact missing or insufficient owner receipt for *profile_id*."""
    spec = OWNER_RECEIPT_SPECS.get(profile_id)
    if spec is None:
        return {
            "profileId": profile_id,
            "present": False,
            "live": False,
            "requiredKind": "unknown-consumer-owner-live-receipt",
            "owner": "unregistered-profile",
            "reason": f"unknown_consumer_profile:{profile_id}",
        }
    observed = root / spec["observedSourceOnlyReceipt"]
    live = False
    observed_status = "missing"
    digest = None
    if observed.is_file():
        raw = observed.read_bytes()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        live_apply = bool(payload.get("liveApply"))
        live_activation = bool(payload.get("liveActivation"))
        packets = payload.get("packets") if isinstance(payload, dict) else None
        enabled = False
        if isinstance(packets, list):
            enabled = any(
                isinstance(item, dict) and item.get("enabled") is True and item.get("liveApply") is True
                for item in packets
            )
        live = live_apply and live_activation and enabled
        observed_status = (
            "live-owner-receipt"
            if live
            else "source-only disabled packets; liveApply=false"
        )
    return {
        "profileId": profile_id,
        "present": observed.is_file(),
        "live": live,
        "requiredKind": spec["requiredKind"],
        "owner": spec["owner"],
        "observedPath": spec["observedSourceOnlyReceipt"],
        "observedDigest": digest,
        "observedStatus": observed_status,
        "reason": None if live else "missing_live_owner_receipt",
    }


def inspect_issuer_receipt() -> dict[str, Any]:
    present = bool(os.environ.get(ISSUER_ENV, "").strip())
    authority = os.environ.get(ISSUER_AUTHORITY_ENV, "").strip().lower()
    live = present and authority in {"secretref", "gsm"}
    return {
        "requiredKind": "eval-runner-issuer-secretref",
        "owner": "Eval Runner issuer (SecretRef / process env, never Git)",
        "envName": ISSUER_ENV,
        "authorityEnvName": ISSUER_AUTHORITY_ENV,
        "authority": authority or None,
        "present": present,
        "live": live,
        "reason": None if live else f"missing_owner_receipt:{ISSUER_ENV}+{ISSUER_AUTHORITY_ENV}=secretref",
    }


def inspect_isolator_receipt() -> dict[str, Any]:
    import shutil

    bwrap = shutil.which("bwrap")
    live = bool(bwrap)
    return {
        "requiredKind": "linux-bwrap-path-allowlist-isolator",
        "owner": "Sealed Linux confined executor (ADR 0009)",
        "present": live,
        "live": live,
        "path": bwrap,
        "reason": None if live else "missing_owner_receipt:bwrap",
    }


def inspect_sealed_image_receipt() -> dict[str, Any]:
    raw = os.environ.get(SEALED_IMAGE_ENV, "").strip()
    pinned = "@sha256:" in raw and len(raw.split("@sha256:", 1)[-1]) >= 64
    return {
        "requiredKind": "sealed-linux-evaluator-image-digest",
        "owner": "Sealed Linux evaluation image pin",
        "envName": SEALED_IMAGE_ENV,
        "present": bool(raw),
        "live": pinned,
        "observed": "digest-pinned" if pinned else (raw[:48] + "…" if raw else None),
        "reason": None if pinned else f"missing_owner_receipt:{SEALED_IMAGE_ENV}@sha256",
    }


@dataclass(frozen=True)
class ConsumerProfileDriver:
    """Confined Linux driver bound to one consumer capability profile."""

    profile_id: str
    adapter_kind: str = DRIVER_KIND
    driver_version: str = DRIVER_VERSION

    def binding(self, root: Path) -> dict[str, Any]:
        owner = inspect_owner_receipt(root, self.profile_id)
        issuer = inspect_issuer_receipt()
        image = inspect_sealed_image_receipt()
        isolator = inspect_isolator_receipt()
        missing = [
            row
            for row in (owner, issuer, image, isolator)
            if not row.get("live")
        ]
        return {
            "schemaVersion": SCHEMA_VERSION,
            "kind": self.adapter_kind,
            "driverVersion": self.driver_version,
            "profileId": self.profile_id,
            "adapterDigest": adapter_digest(profile_id=self.profile_id),
            "runtimeDigest": runtime_digest(),
            "ownerReceipt": owner,
            "issuerReceipt": issuer,
            "sealedImageReceipt": image,
            "isolatorReceipt": isolator,
            "missingOwnerReceipts": missing,
            "liveConsumerActor": False,
            "guiLaunch": False,
        }

    def toolchain(self, root: Path) -> dict[str, Any]:
        bound = self.binding(root)
        return {
            "runtime_profile": self.profile_id,
            "consumer_profile_driver": bound,
            "adapter_digest": bound["adapterDigest"],
            "runtime_digest": bound["runtimeDigest"],
        }


def resolve_driver(profile_id: str) -> ConsumerProfileDriver:
    profile = str(profile_id or "").strip()
    if profile not in KNOWN_PROFILES:
        raise ValueError(f"unsupported consumer profile: {profile!r}")
    return ConsumerProfileDriver(profile_id=profile)


def bind_consumer_profile_execute(
    execute: Mapping[str, Any],
    *,
    repo_root: Path,
    toolchain: Optional[Mapping[str, Any]] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (skill_script execute spec, merged toolchain) for a consumer_profile case."""
    profile_id = str(execute.get("profile") or CURSOR_MACOS).strip()
    driver = resolve_driver(profile_id)
    merged = dict(toolchain or {})
    merged.update(driver.toolchain(repo_root))
    script_spec = {
        "kind": "skill_script",
        "script": execute.get("script"),
        "argv": list(execute.get("argv") or []),
        "env": dict(execute.get("env") or {}),
        "timeout_seconds": execute.get("timeout_seconds") or 30,
        "append_input_argv": bool(execute.get("append_input_argv")),
        "name": execute.get("name") or f"{profile_id}:skill_script",
        "version": execute.get("version") or DRIVER_VERSION,
    }
    if execute.get("stdin") is not None:
        script_spec["stdin"] = execute.get("stdin")
    return script_spec, merged
