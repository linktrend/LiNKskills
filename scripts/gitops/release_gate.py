#!/usr/bin/env python3
"""Identity-bound short release-gate evidence for promotion.

This module never reruns the full suite, never mutates GitHub, and never
promotes a branch.  It only writes or verifies a machine-readable inventory
bound to the exact candidate identity consumed by the delivery controller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_delivery_profile import (  # noqa: E402
    IDENTITY_FIELDS,
    MUTATION_MARKERS,
    DeliveryProfileError,
    digest_json,
    identity_digest,
)

SCHEMA_VERSION = 1
EVIDENCE_KIND = "release-gate-evidence"
REQUIRED_IDENTITY = tuple(IDENTITY_FIELDS)
FULL_PROFILE_MARKERS = ("run_delivery_profile.py", "run_delivery_profile")


class ReleaseGateError(ValueError):
    """A deterministic release-evidence failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _identity_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if hasattr(value, "to_dict") and callable(value.to_dict):
        value = value.to_dict()
    payload = _mapping(value)
    if payload is None:
        return None
    return {field: payload[field] for field in REQUIRED_IDENTITY if field in payload}


def _commands(value: Any) -> list[list[str]] | None:
    if not isinstance(value, list):
        return None
    rows: list[list[str]] = []
    for item in value:
        if isinstance(item, Mapping) and isinstance(item.get("argv"), list):
            argv = item["argv"]
        else:
            argv = item
        if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) and arg for arg in argv):
            return None
        rows.append(list(argv))
    return rows


def _declares_full_suite(commands: list[list[str]]) -> bool:
    for argv in commands:
        names = {Path(arg).name for arg in argv}
        if names & set(FULL_PROFILE_MARKERS) and "full" in argv:
            return True
    return False


def _declares_mutation(commands: list[list[str]]) -> bool:
    return any(Path(argv[0]).name.lower() in MUTATION_MARKERS for argv in commands if argv)


def evidence_from_inventory(
    inventory: Mapping[str, Any],
    *,
    full_suite_invoked: bool = False,
) -> dict[str, Any]:
    """Build controller-consumed release evidence from a profile inventory."""

    if full_suite_invoked or bool(inventory.get("fullSuiteInvoked")):
        raise ReleaseGateError("full_suite_reentered", "release evidence must not rerun the full suite")
    if inventory.get("profile") != "release":
        raise ReleaseGateError("release_profile_required", "inventory profile must be release")
    commands = _commands(inventory.get("commands"))
    if not commands:
        raise ReleaseGateError("evidence_empty", "release inventory commands are missing or empty")
    if _declares_full_suite(commands):
        raise ReleaseGateError("full_suite_reentered", "release commands must not invoke the full profile")
    if _declares_mutation(commands):
        raise ReleaseGateError("release_gate_mutating", "release commands must be non-mutating")
    identity = _identity_dict(inventory.get("identity"))
    if identity is None or set(identity) != set(REQUIRED_IDENTITY):
        raise ReleaseGateError("identity_missing", "release inventory is not bound to a complete identity")
    try:
        digest = identity_digest(identity)
    except (ValueError, DeliveryProfileError) as exc:
        raise ReleaseGateError("identity_invalid", str(exc)) from exc
    observed = inventory.get("identityDigest")
    if observed not in {None, digest}:
        raise ReleaseGateError("identity_mismatch", "inventory identityDigest does not match identity")
    ok = inventory.get("ok") is True and inventory.get("complete") is True and not inventory.get("workspaceMutated")
    status = "passed" if ok and int(inventory.get("failedCount") or 0) == 0 else "failed"
    evidence = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": EVIDENCE_KIND,
        "status": status,
        "testProfile": "release",
        "fullSuiteInvoked": False,
        "ok": status == "passed",
        "complete": bool(inventory.get("complete")),
        "workspaceMutated": bool(inventory.get("workspaceMutated")),
        "identity": identity,
        "identityDigest": digest,
        "inventoryDigest": inventory.get("inventoryDigest") or digest_json(
            {key: inventory.get(key) for key in ("profile", "boundary", "risk", "commands", "identityDigest")}
        ),
        "commands": commands,
        "executedCount": int(inventory.get("executedCount") or 0),
        "failedCount": int(inventory.get("failedCount") or 0),
        "omittedCount": int(inventory.get("omittedCount") or 0),
    }
    return evidence


def has_release_evidence_shape(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False
    if payload.get("kind") == EVIDENCE_KIND:
        return True
    nested = payload.get("evidence")
    return isinstance(nested, Mapping) and nested.get("kind") == EVIDENCE_KIND


def _evidence_body(payload: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    nested = payload.get("evidence")
    if isinstance(nested, Mapping) and nested.get("kind") == EVIDENCE_KIND:
        return nested
    if payload.get("kind") == EVIDENCE_KIND:
        return payload
    return None


def verify_release_evidence(
    payload: Mapping[str, Any] | None,
    expected_identity: Any = None,
    *,
    require: bool = False,
) -> dict[str, Any]:
    """Return a machine-readable verdict for missing/empty/stale/failed/success."""

    def verdict(accepted: bool, code: str, detail: str) -> dict[str, Any]:
        return {
            "accepted": accepted,
            "status": "PASS" if accepted else "HOLD",
            "code": code,
            "detail": detail,
        }

    if payload is None:
        return verdict(False, "evidence_missing", "release evidence is missing")
    if not isinstance(payload, Mapping) or not payload:
        return verdict(False, "evidence_empty", "release evidence is empty")

    if bool(payload.get("fullSuiteInvoked")):
        return verdict(False, "full_suite_reentered", "staging/main promotion must reuse the matching receipt")

    body = _evidence_body(payload)
    if body is None:
        if require:
            return verdict(False, "evidence_missing", "identity-bound release evidence is required")
        return verdict(True, "accepted", "short release checks passed without a full-suite rerun")

    if body.get("kind") != EVIDENCE_KIND:
        return verdict(False, "evidence_missing", "release evidence kind is missing")
    if body.get("schemaVersion") != SCHEMA_VERSION:
        return verdict(False, "evidence_empty", "release evidence schema is unsupported or empty")

    commands = _commands(body.get("commands"))
    if not commands:
        return verdict(False, "evidence_empty", "release evidence commands are missing or empty")
    if _declares_full_suite(commands):
        return verdict(False, "full_suite_reentered", "release evidence must not invoke the full profile")
    if _declares_mutation(commands):
        return verdict(False, "release_gate_mutating", "release evidence declares a mutating command")

    identity = _identity_dict(body.get("identity"))
    if identity is None or set(identity) != set(REQUIRED_IDENTITY):
        return verdict(False, "evidence_empty", "release evidence identity is missing")
    try:
        digest = identity_digest(identity)
    except (ValueError, DeliveryProfileError):
        return verdict(False, "evidence_stale", "release evidence identity is malformed")
    if str(body.get("identityDigest") or "") != digest:
        return verdict(False, "evidence_stale", "release evidence identityDigest does not match identity")

    expected = _identity_dict(expected_identity) or _identity_dict(payload.get("expectedIdentity"))
    if expected is not None:
        try:
            expected_digest = identity_digest(expected) if set(expected) == set(REQUIRED_IDENTITY) else ""
        except (ValueError, DeliveryProfileError):
            expected_digest = ""
        if expected.get("headCommit") and identity.get("headCommit") != expected.get("headCommit"):
            return verdict(False, "evidence_stale", "release evidence is not bound to the exact promotion commit")
        if expected.get("gitTree") and identity.get("gitTree") != expected.get("gitTree"):
            return verdict(False, "evidence_stale", "release evidence is not bound to the exact promotion tree")
        if expected.get("repository") and identity.get("repository") != expected.get("repository"):
            return verdict(False, "evidence_stale", "release evidence is not bound to the exact repository")
        if expected_digest and expected_digest != digest:
            return verdict(False, "evidence_stale", "release evidence identity digest does not match the candidate")

    profile = str(body.get("testProfile") or payload.get("testProfile") or "release").strip().lower()
    if profile != "release":
        return verdict(False, "release_profile_required", "promotion release checks must use the release profile")

    status = str(body.get("status") or payload.get("status") or "").strip().lower()
    ok = body.get("ok") is True and body.get("complete") is True and not body.get("workspaceMutated")
    if not ok or status not in {"passed", "success", "successful", "green"} or int(body.get("failedCount") or 0) != 0:
        return verdict(False, "release_gate_failed", "short release checks did not pass")
    return verdict(True, "accepted", "short release checks passed without a full-suite rerun")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseGateError("evidence_missing", f"release evidence file is missing: {path}") from exc
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ReleaseGateError("evidence_empty", f"release evidence file is unreadable: {exc}") from exc


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    write = commands.add_parser("write")
    write.add_argument("--inventory", required=True, type=Path)
    write.add_argument("--out", required=True, type=Path)
    write.add_argument("--full-suite-invoked", action="store_true")

    verify = commands.add_parser("verify")
    verify.add_argument("--evidence", type=Path)
    verify.add_argument("--identity", type=Path)
    verify.add_argument("--require", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "write":
            inventory = load_json(args.inventory)
            if not isinstance(inventory, Mapping):
                raise ReleaseGateError("evidence_empty", "release inventory is empty")
            evidence = evidence_from_inventory(inventory, full_suite_invoked=args.full_suite_invoked)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _print(evidence)
            return 0 if evidence["ok"] else 1
        evidence_payload = load_json(args.evidence) if args.evidence is not None else None
        identity_payload = load_json(args.identity) if args.identity is not None else None
        verdict = verify_release_evidence(
            evidence_payload if isinstance(evidence_payload, Mapping) or evidence_payload is None else {},
            identity_payload,
            require=args.require or args.evidence is not None,
        )
        _print(verdict)
        return 0 if verdict["accepted"] else 1
    except ReleaseGateError as exc:
        _print({"accepted": False, "status": "HOLD", "code": exc.code, "detail": exc.detail})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
