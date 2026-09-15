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
# Never log process issuer material; inspect length/presence only.
ISSUER_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"
ISSUER_AUTHORITY_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_AUTHORITY"
ISSUER_ID_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_ID"
ISSUER_SECRET_REF_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_REF"
ISSUER_SECRET_VERSION_ENV = "LINKSKILLS_EVAL_RUNNER_ISSUER_SECRET_VERSION"
CURSOR_SHARED_GLOBAL_MUTATION_ENV = "LINKSKILLS_CURSOR_SHARED_GLOBAL_MUTATION"
SEALED_IMAGE_ENV = "LINKSKILLS_SEALED_CERT_IMAGE"
MIN_PROCESS_ISSUER_BITS = 256
TRUSTED_ISSUER_AUTHORITIES = frozenset({"secretref", "gsm"})
EXPLICIT_TRUE = frozenset({"1", "true", "yes", "declared", "required", "shared", "global"})
CURSOR_PROJECT_SCOPED_KIND = "cursor-project-scoped-owner-live-receipt"
XP02_CURSOR_KIND = "xp-02-cursor-owner-live-receipt"

OWNER_RECEIPT_SPECS: dict[str, dict[str, str]] = {
    CURSOR_MACOS: {
        "requiredKind": CURSOR_PROJECT_SCOPED_KIND,
        "owner": "LiNKskills project-scoped Cursor canary owner",
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

XP02_CURSOR_SPEC: dict[str, str] = {
    "requiredKind": XP02_CURSOR_KIND,
    "owner": "XP-02 shared/global Cursor configuration owner",
    "observedSourceOnlyReceipt": (
        "evidence/end-to-end-delivery/ed-05/source-consumer-packet-receipt.json"
    ),
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


def _truthy_declared(value: str) -> bool:
    return value.strip().lower() in EXPLICIT_TRUE


def shared_global_cursor_mutation_declared(root: Path | None = None) -> bool:
    """XP-02 applies only when a shared/global Cursor mutation is explicitly declared."""
    if _truthy_declared(os.environ.get(CURSOR_SHARED_GLOBAL_MUTATION_ENV, "")):
        return True
    if root is None:
        return False
    spec = OWNER_RECEIPT_SPECS[CURSOR_MACOS]
    observed = root / spec["observedSourceOnlyReceipt"]
    if not observed.is_file():
        return False
    try:
        payload = json.loads(observed.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    for key in ("sharedOrGlobalCursorMutation", "sharedGlobalCursorMutation"):
        raw = payload.get(key)
        if raw is True or (isinstance(raw, str) and _truthy_declared(raw)):
            return True
    return False


def _observe_owner_packet(root: Path, spec: Mapping[str, str]) -> dict[str, Any]:
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
        "present": observed.is_file(),
        "live": live,
        "requiredKind": spec["requiredKind"],
        "owner": spec["owner"],
        "observedPath": spec["observedSourceOnlyReceipt"],
        "observedDigest": digest,
        "observedStatus": observed_status,
        "reason": None if live else "missing_live_owner_receipt",
    }


def inspect_owner_receipt(root: Path, profile_id: str) -> dict[str, Any]:
    """Return the default owner receipt for *profile_id*.

    ``cursor-macos`` uses project-scoped owner proof. XP-02 is not this default.
    """
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
    row = _observe_owner_packet(root, spec)
    row["profileId"] = profile_id
    if profile_id == CURSOR_MACOS:
        row["xp"] = None
        row["requiredWhen"] = None
    return row


def inspect_xp02_cursor_receipt(root: Path) -> dict[str, Any]:
    """XP-02 shared/global Cursor owner receipt; required only when declared."""
    declared = shared_global_cursor_mutation_declared(root)
    row = _observe_owner_packet(root, XP02_CURSOR_SPEC)
    row["profileId"] = CURSOR_MACOS
    row["xp"] = "XP-02"
    row["requiredWhen"] = "sharedOrGlobalCursorMutation"
    row["required"] = declared
    if not declared:
        row["live"] = False
        row["reason"] = "xp02_not_required_project_scoped_default"
    return row


def inspect_owner_receipts(root: Path, profile_id: str) -> list[dict[str, Any]]:
    """Return required owner receipts. XP-02 is appended only when declared."""
    rows = [inspect_owner_receipt(root, profile_id)]
    if profile_id == CURSOR_MACOS and shared_global_cursor_mutation_declared(root):
        rows.append(inspect_xp02_cursor_receipt(root))
    return rows


def _process_issuer_bits(raw: str) -> int:
    """Bit length of process issuer material. Never log or return the value."""
    return len(raw.encode("utf-8")) * 8


def _immutable_secret_version(version: str, secret_ref: str) -> bool:
    if not version or not secret_ref:
        return False
    if "latest" in version.lower() or "latest" in secret_ref.lower():
        return False
    return True


def inspect_issuer_receipt() -> dict[str, Any]:
    """Observe issuer custody without reading SecretRef values.

    Live only with a trusted authority kind plus an immutable SecretRef/version
    and an explicit issuer identity. An authority label alone, ``latest``, or
    weak process material below 256 bits cannot make custody live.
    """
    raw = os.environ.get(ISSUER_ENV, "").strip()
    present = bool(raw)
    weak_process = present and _process_issuer_bits(raw) < MIN_PROCESS_ISSUER_BITS
    authority = os.environ.get(ISSUER_AUTHORITY_ENV, "").strip().lower()
    issuer_identity = os.environ.get(ISSUER_ID_ENV, "").strip()
    secret_ref = os.environ.get(ISSUER_SECRET_REF_ENV, "").strip()
    secret_version = os.environ.get(ISSUER_SECRET_VERSION_ENV, "").strip()
    authority_ok = authority in TRUSTED_ISSUER_AUTHORITIES
    version_ok = _immutable_secret_version(secret_version, secret_ref)
    identity_ok = bool(issuer_identity)
    live = (
        not weak_process
        and authority_ok
        and version_ok
        and identity_ok
    )
    if live:
        reason = None
    elif weak_process:
        reason = "weak_process_issuer_material"
    elif authority_ok and not (secret_ref and version_ok and identity_ok):
        if secret_version and "latest" in f"{secret_version} {secret_ref}".lower():
            reason = "mutable_secret_version_rejected"
        elif not secret_ref or not secret_version or not identity_ok:
            reason = "authority_label_insufficient"
        else:
            reason = "authority_label_insufficient"
    elif secret_version and "latest" in f"{secret_version} {secret_ref}".lower():
        reason = "mutable_secret_version_rejected"
    else:
        reason = (
            f"missing_owner_receipt:{ISSUER_SECRET_REF_ENV}+"
            f"{ISSUER_SECRET_VERSION_ENV}+{ISSUER_ID_ENV}"
        )
    return {
        "requiredKind": "eval-runner-issuer-secretref",
        "owner": "Eval Runner issuer (SecretRef / process env, never Git)",
        "envName": ISSUER_ENV,
        "authorityEnvName": ISSUER_AUTHORITY_ENV,
        "secretRefEnvName": ISSUER_SECRET_REF_ENV,
        "secretVersionEnvName": ISSUER_SECRET_VERSION_ENV,
        "issuerIdEnvName": ISSUER_ID_ENV,
        "authority": authority or None,
        "secretRefPresent": bool(secret_ref),
        "secretVersionImmutable": version_ok,
        "issuerIdentityPresent": identity_ok,
        "processMaterialPresent": present,
        "processMaterialMeetsMinimumBits": present and not weak_process,
        "present": present or bool(secret_ref),
        "live": live,
        "reason": reason,
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
        owners = inspect_owner_receipts(root, self.profile_id)
        issuer = inspect_issuer_receipt()
        image = inspect_sealed_image_receipt()
        isolator = inspect_isolator_receipt()
        # Qualification precedes publication and consumer activation. Requiring
        # an activated consumer here creates a cycle and conflates separate gates.
        # The driver still requires real execution, issuer custody and isolation.
        missing = [row for row in (issuer, image, isolator) if not row.get("live")]
        return {
            "schemaVersion": SCHEMA_VERSION,
            "kind": self.adapter_kind,
            "driverVersion": self.driver_version,
            "profileId": self.profile_id,
            "adapterDigest": adapter_digest(profile_id=self.profile_id),
            "runtimeDigest": runtime_digest(),
            "ownerReceipt": owners[0],
            "ownerReceipts": owners,
            "issuerReceipt": issuer,
            "sealedImageReceipt": image,
            "isolatorReceipt": isolator,
            "missingOwnerReceipts": missing,
            "pendingConsumerReceipts": [row for row in owners if not row.get("live")],
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
