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
import re
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
ISSUER_SECRETREF_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_SECRETREF"
ISSUER_SECRETREF_VERSION_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_SECRETREF_VERSION"
ISSUER_ID_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_ID"
CURSOR_SHARED_GLOBAL_MUTATION_ENV = "LINKSKILLS_CURSOR_SHARED_GLOBAL_MUTATION"
SEALED_IMAGE_ENV = "LINKSKILLS_SEALED_CERT_IMAGE"

ISSUER_MIN_KEY_BITS = 256
_TRUSTED_ISSUER_AUTHORITIES = frozenset({"secretref", "gsm"})
_MUTABLE_SECRETREF_VERSIONS = frozenset({"latest", "current", "head", "default", "tip"})
_TRUE_FLAGS = frozenset({"1", "true", "yes", "required", "shared", "global"})
_SECRETREF_NAME_RE = re.compile(r"^LINKTREND_[A-Z][A-Z0-9_]{7,}$")
_SECRETREF_RESOURCE_RE = re.compile(
    r"^projects/[^/]+/secrets/[A-Za-z0-9_-]+/versions/[1-9][0-9]*$"
)
_SECRETREF_URI_RE = re.compile(r"^secretref:LINKTREND_[A-Z][A-Z0-9_]{7,}$")
_IMMUTABLE_VERSION_RE = re.compile(r"^(?:[1-9][0-9]*|[0-9a-fA-F]{64})$")
_HEX_KEY_RE = re.compile(r"^[0-9a-fA-F]+$")

CURSOR_PROJECT_SCOPED_KIND = "ed-09-cursor-project-scoped-owner-live-receipt"
CURSOR_PROJECT_SCOPED_OWNER = "LiNKskills project-scoped Cursor owner"
CURSOR_XP02_KIND = "xp-02-cursor-owner-live-receipt"
CURSOR_XP02_OWNER = "XP-02 Cursor shared/global configuration owner"

OWNER_RECEIPT_SPECS: dict[str, dict[str, str]] = {
    CURSOR_MACOS: {
        "requiredKind": CURSOR_PROJECT_SCOPED_KIND,
        "owner": CURSOR_PROJECT_SCOPED_OWNER,
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


def _truthy_flag(raw: str) -> bool:
    return raw.strip().lower() in _TRUE_FLAGS


def _cursor_shared_global_mutation_required(root: Path, payload: Mapping[str, Any] | None) -> bool:
    """XP-02 is required only when an actual shared/global Cursor mutation is declared."""
    if _truthy_flag(os.environ.get(CURSOR_SHARED_GLOBAL_MUTATION_ENV, "")):
        return True
    packet_path = root / "configs/consumer-activation/ed-05-cursor-owner-packet.json"
    packet: Mapping[str, Any] = {}
    if packet_path.is_file():
        try:
            loaded = json.loads(packet_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            packet = loaded
    for source in (payload or {}, packet):
        activation = source.get("activation") if isinstance(source.get("activation"), dict) else {}
        for key in ("sharedGlobalMutation", "sharedGlobalCursorMutation", "xp02Required"):
            if source.get(key) is True or activation.get(key) is True:
                return True
        scope = str(source.get("scope") or activation.get("scope") or "").strip().lower()
        if scope in {"shared", "global", "shared/global"}:
            return True
    packets = payload.get("packets") if isinstance(payload, dict) else None
    if isinstance(packets, list):
        for item in packets:
            if not isinstance(item, dict):
                continue
            if str(item.get("packetId") or "") != "ed-05-cursor":
                continue
            if item.get("sharedGlobalMutation") is True or item.get("xp02Required") is True:
                return True
            scope = str(item.get("scope") or "").strip().lower()
            if scope in {"shared", "global", "shared/global"}:
                return True
    return False


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
    payload: dict[str, Any] = {}
    if observed.is_file():
        raw = observed.read_bytes()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        try:
            loaded = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            loaded = {}
        if isinstance(loaded, dict):
            payload = loaded
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
    required_kind = spec["requiredKind"]
    owner = spec["owner"]
    scope = "declared"
    xp02_required = False
    if profile_id == CURSOR_MACOS:
        xp02_required = _cursor_shared_global_mutation_required(root, payload)
        if xp02_required:
            required_kind = CURSOR_XP02_KIND
            owner = CURSOR_XP02_OWNER
            scope = "shared/global"
            live = False
            if observed_status != "missing":
                observed_status = "xp-02 required for shared/global Cursor mutation; project-scoped proof is insufficient"
        else:
            required_kind = CURSOR_PROJECT_SCOPED_KIND
            owner = CURSOR_PROJECT_SCOPED_OWNER
            scope = "project-scoped"
    return {
        "profileId": profile_id,
        "present": observed.is_file(),
        "live": live,
        "requiredKind": required_kind,
        "owner": owner,
        "scope": scope,
        "xp02Required": xp02_required if profile_id == CURSOR_MACOS else False,
        "observedPath": spec["observedSourceOnlyReceipt"],
        "observedDigest": digest,
        "observedStatus": observed_status,
        "reason": None if live else "missing_live_owner_receipt",
    }


def _issuer_process_key_bit_strength(raw: str) -> int:
    """Return process-key entropy in bits. Never log or persist *raw*."""
    stripped = raw.strip()
    if not stripped:
        return 0
    if _HEX_KEY_RE.fullmatch(stripped) and len(stripped) % 2 == 0:
        return (len(stripped) // 2) * 8
    return len(stripped.encode("utf-8")) * 8


def _trusted_secretref(raw: str) -> bool:
    value = raw.strip()
    if not value:
        return False
    return bool(
        _SECRETREF_NAME_RE.fullmatch(value)
        or _SECRETREF_RESOURCE_RE.fullmatch(value)
        or _SECRETREF_URI_RE.fullmatch(value)
    )


def _immutable_secretref_version(raw: str) -> bool:
    value = raw.strip()
    if not value or value.strip().lower() in _MUTABLE_SECRETREF_VERSIONS:
        return False
    return bool(_IMMUTABLE_VERSION_RE.fullmatch(value))


def inspect_issuer_receipt() -> dict[str, Any]:
    """Qualify issuer custody without treating a raw process key as live.

    Live custody requires an operator-provided immutable SecretRef plus version
    and an explicit issuer identity binding. A process key plus authority
    label is never sufficient. If a process key is present, it must be at
    least 256 bits; the value is never logged or stored.
    """
    process_key = os.environ.get(ISSUER_ENV, "").strip()
    authority = os.environ.get(ISSUER_AUTHORITY_ENV, "").strip().lower()
    secretref = os.environ.get(ISSUER_SECRETREF_ENV, "").strip()
    version = os.environ.get(ISSUER_SECRETREF_VERSION_ENV, "").strip()
    issuer_id = os.environ.get(ISSUER_ID_ENV, "").strip()

    process_key_present = bool(process_key)
    key_bits = _issuer_process_key_bit_strength(process_key) if process_key_present else None
    key_meets_min = None if key_bits is None else key_bits >= ISSUER_MIN_KEY_BITS
    secretref_trusted = _trusted_secretref(secretref)
    version_immutable = _immutable_secretref_version(version)
    issuer_identity_bound = bool(issuer_id)
    trusted_authority = authority in _TRUSTED_ISSUER_AUTHORITIES
    process_key_blocks_live = process_key_present and key_meets_min is False

    live = (
        trusted_authority
        and secretref_trusted
        and version_immutable
        and issuer_identity_bound
        and not process_key_blocks_live
    )
    reasons: list[str] = []
    if not trusted_authority:
        reasons.append(f"missing_owner_receipt:{ISSUER_AUTHORITY_ENV}=secretref")
    if not secretref_trusted:
        reasons.append(f"missing_owner_receipt:{ISSUER_SECRETREF_ENV}")
    if not version_immutable:
        reasons.append(f"missing_owner_receipt:{ISSUER_SECRETREF_VERSION_ENV}=immutable")
    if not issuer_identity_bound:
        reasons.append(f"missing_owner_receipt:{ISSUER_ID_ENV}")
    if process_key_blocks_live:
        reasons.append("issuer_process_key_below_256_bits")
    if process_key_present and not (secretref_trusted and version_immutable and issuer_identity_bound):
        reasons.append("raw_process_key_is_not_live_issuer_custody")
    return {
        "requiredKind": "eval-runner-issuer-secretref",
        "owner": "Eval Runner issuer (immutable SecretRef / version, never Git)",
        "envName": ISSUER_ENV,
        "authorityEnvName": ISSUER_AUTHORITY_ENV,
        "secretRefEnvName": ISSUER_SECRETREF_ENV,
        "secretRefVersionEnvName": ISSUER_SECRETREF_VERSION_ENV,
        "issuerIdEnvName": ISSUER_ID_ENV,
        "authority": authority or None,
        "secretRefPresent": secretref_trusted,
        "secretRefVersionImmutable": version_immutable,
        "issuerIdentityBound": issuer_identity_bound,
        "processKeyPresent": process_key_present,
        "keyMaterialMeetsMinBits": key_meets_min,
        "present": secretref_trusted,
        "live": live,
        "reason": None if live else ",".join(reasons) if reasons else "eval_pending",
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
