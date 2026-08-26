"""Fail-closed PKT-26 definition-of-done reconciliation.

The command evaluates a supplied receipt document only.  It never queries
another repository, provider, deployment, or runtime.  Missing or
identity-incomplete evidence therefore produces a truthful ``HOLD`` report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


DECISIONS = {"COMPLETE", "HOLD"}
CLASSIFICATIONS = {"proven", "not_proven", "partial", "blocked_external", "excluded"}
EVIDENCE_CLASSES = {"source", "consumer", "hosted/stage", "VPS", "E2E", "production"}
REQUIRED_DEPENDENCIES = ("PKT-25", "XPKT-04", "XPKT-05")
REQUIRED_SLOTS = ("provider", "platform", "autowork", "openclaw", "hosted_stage", "vps", "production", "independent_verification")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
RECEIPT_DIGEST_FIELDS = {"receipt_digest", "receiptDigest", "receipt_sha256", "receiptSha256"}


class ReconciliationError(ValueError):
    """Raised when the input is structurally malformed."""


def _is_sha(value: Any, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and bool(pattern.fullmatch(value))


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _receipt_file_digests(path: Path) -> tuple[set[str], Mapping[str, Any] | None]:
    """Return raw/canonical digests and a parsed receipt payload."""

    raw = path.read_bytes()
    digests = {hashlib.sha256(raw).hexdigest()}
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return digests, None
    if isinstance(payload, Mapping):
        without_digest = {
            key: value for key, value in payload.items() if key not in RECEIPT_DIGEST_FIELDS
        }
        digests.add(_digest(payload))
        digests.add(_digest(without_digest))
        return digests, payload
    return digests, None


def _resolve_receipt_reference(
    receipt_ref: Any,
    receipt_digest: Any,
    *,
    label: str,
    receipt_root: Path,
) -> tuple[list[str], Mapping[str, Any] | None, Path | None]:
    """Resolve a receipt reference, verify its digest, and parse its payload."""

    if not isinstance(receipt_ref, str) or not receipt_ref.strip():
        return [], None, None
    if not isinstance(receipt_digest, str) or not SHA256_RE.fullmatch(receipt_digest):
        return [f"{label}:receipt_digest_invalid"], None, None
    reference = receipt_ref.strip()
    if reference.startswith("opaque:"):
        return [f"{label}:receipt_ref_unresolvable"], None, None
    if any(character.isspace() for character in reference):
        return [f"{label}:receipt_ref_invalid"], None, None
    candidate = Path(reference)
    if candidate.is_absolute() or ".." in candidate.parts:
        return [f"{label}:receipt_ref_outside_root"], None, None
    candidate = receipt_root / candidate
    if candidate.is_symlink():
        return [f"{label}:receipt_ref_unresolvable"], None, None
    try:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(receipt_root.resolve())
        except ValueError:
            return [f"{label}:receipt_ref_outside_root"], None, None
    except OSError:
        return [f"{label}:receipt_ref_unresolvable"], None, None
    if not resolved.is_file() or resolved.is_symlink():
        return [f"{label}:receipt_ref_unresolvable"], None, None
    try:
        digests, payload = _receipt_file_digests(resolved)
    except OSError:
        return [f"{label}:receipt_ref_unreadable"], None, resolved
    if receipt_digest not in digests:
        return [f"{label}:receipt_digest_mismatch"], payload, resolved
    if payload is None:
        return [f"{label}:receipt_payload_invalid"], None, resolved
    return [], payload, resolved


def _identity_problems(slot: Mapping[str, Any], *, environment_required: bool) -> list[str]:
    problems: list[str] = []
    for field in ("repository", "ref", "commit", "tree", "command_or_profile_digest", "result_digest", "rollback_ref", "handoff_ref"):
        if not isinstance(slot.get(field), str) or not slot[field].strip():
            problems.append(f"missing_{field}")
    if not _is_sha(slot.get("commit"), SHA40_RE):
        problems.append("invalid_commit")
    if not _is_sha(slot.get("tree"), SHA40_RE):
        problems.append("invalid_tree")
    for field in ("command_or_profile_digest", "result_digest"):
        if not _is_sha(slot.get(field), SHA256_RE):
            problems.append(f"invalid_{field}")
    if environment_required and not isinstance(slot.get("environment"), str):
        problems.append("missing_environment")
    return problems


def _validate_dependencies(
    payload: Mapping[str, Any], *, receipt_root: Path
) -> tuple[list[str], dict[str, Mapping[str, Any]], dict[str, str]]:
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, Mapping):
        return ["dependencies_missing"], {}, {}
    problems: list[str] = []
    receipts: dict[str, Mapping[str, Any]] = {}
    receipt_digests: dict[str, str] = {}
    for dependency in REQUIRED_DEPENDENCIES:
        item = dependencies.get(dependency)
        if not isinstance(item, Mapping):
            problems.append(f"{dependency}:receipt_missing")
            continue
        if item.get("required") is not True:
            problems.append(f"{dependency}:required_flag_missing")
        if item.get("admission") not in {"ADMITTED", "ACCEPTED", "PROVEN"}:
            problems.append(f"{dependency}:not_admitted")
        if not isinstance(item.get("receipt_ref"), str) or not item["receipt_ref"].strip():
            problems.append(f"{dependency}:receipt_ref_missing")
        if not _is_sha(item.get("receipt_digest"), SHA256_RE):
            problems.append(f"{dependency}:receipt_digest_invalid")
        reference_problems, receipt, resolved = _resolve_receipt_reference(
            item.get("receipt_ref"),
            item.get("receipt_digest"),
            label=dependency,
            receipt_root=receipt_root,
        )
        problems.extend(reference_problems)
        if receipt is not None and resolved is not None and not reference_problems:
            problems.extend(_receipt_identity_problems(receipt, dependency))
            packet = _receipt_value(receipt, "packet", "packet_id", "packetId")
            dependency_claim = receipt.get("dependency")
            if packet != dependency and dependency_claim != dependency:
                problems.append(f"{dependency}:receipt_packet_mismatch")
            key = str(resolved)
            receipts[key] = receipt
            receipt_digests[key] = str(item["receipt_digest"])
    return problems, receipts, receipt_digests


def _validate_slots(
    payload: Mapping[str, Any], *, receipt_root: Path
) -> tuple[
    dict[str, list[str]],
    dict[str, Mapping[str, Any]],
    dict[str, str],
    dict[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
]:
    slots = payload.get("receipt_slots")
    if not isinstance(slots, Sequence) or isinstance(slots, (str, bytes, bytearray)):
        raise ReconciliationError("receipt_slots_missing")
    by_name = {item.get("slot"): item for item in slots if isinstance(item, Mapping)}
    problems: dict[str, list[str]] = {}
    receipts: dict[str, Mapping[str, Any]] = {}
    receipt_digests: dict[str, str] = {}
    bindings: dict[str, tuple[Mapping[str, Any], Mapping[str, Any]]] = {}
    for slot_name in REQUIRED_SLOTS:
        slot = by_name.get(slot_name)
        if not isinstance(slot, Mapping):
            problems[slot_name] = ["slot_missing"]
            continue
        slot_problems: list[str] = []
        if slot.get("supplied") is not True:
            slot_problems.append("not_supplied")
        for field in ("receipt_ref", "receipt_digest"):
            if not isinstance(slot.get(field), str) or not slot[field].strip():
                slot_problems.append(f"{field}_missing")
        if isinstance(slot.get("receipt_digest"), str) and not SHA256_RE.fullmatch(slot["receipt_digest"]):
            slot_problems.append("receipt_digest_invalid")
        reference_problems, receipt, resolved = _resolve_receipt_reference(
            slot.get("receipt_ref"),
            slot.get("receipt_digest"),
            label=slot_name,
            receipt_root=receipt_root,
        )
        slot_problems.extend(reference_problems)
        environment_required = slot_name in {"hosted_stage", "vps", "production"}
        slot_problems.extend(_identity_problems(slot, environment_required=environment_required))
        if receipt is not None and not reference_problems:
            slot_problems.extend(_slot_receipt_problems(slot_name, slot, receipt))
        if slot_problems:
            problems[slot_name] = sorted(set(slot_problems))
        if receipt is not None and resolved is not None and not reference_problems:
            key = str(resolved)
            receipts[key] = receipt
            receipt_digests[key] = str(slot["receipt_digest"])
            if not slot_problems:
                bindings[slot_name] = (slot, receipt)
    return problems, receipts, receipt_digests, bindings


def _receipt_value(receipt: Mapping[str, Any], *names: str) -> Any:
    """Read one receipt fact from the supported snake/camel-case aliases."""

    for name in names:
        if name in receipt:
            return receipt[name]
    return None


def _unwrap_identity_source(source: Mapping[str, Any]) -> Mapping[str, Any]:
    """Prefer nested checkout.observed / *.identity payloads over wrapper objects."""

    for key in ("observed", "identity"):
        nested = source.get(key)
        if isinstance(nested, Mapping):
            return nested
    return source


def _receipt_identity(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the exact checkout identity and evidence binding from a receipt."""

    identity = receipt.get("identity")
    source = identity if isinstance(identity, Mapping) else receipt
    values = {
        field: source.get(field)
        for field in ("repository", "ref", "commit", "tree", "evidence_class", "slot")
    }
    for field in ("evidence_class", "slot"):
        if values[field] is None:
            values[field] = receipt.get(field)
    checkout = receipt.get("checkout")
    provider_source = receipt.get("provider_source")
    for nested in (checkout, provider_source):
        if not isinstance(nested, Mapping):
            continue
        inner = _unwrap_identity_source(nested)
        if values["repository"] is None:
            values["repository"] = inner.get("repository", inner.get("origin"))
        for field in ("ref", "commit", "tree"):
            if values[field] is None:
                values[field] = inner.get(field)
    return values


def _receipt_identity_problems(receipt: Mapping[str, Any], label: str) -> list[str]:
    """Require a receipt's repository identity and evidence class to be concrete."""

    identity = _receipt_identity(receipt)
    problems: list[str] = []
    for field in ("repository", "ref", "commit", "tree", "evidence_class"):
        if not isinstance(identity[field], str) or not identity[field].strip():
            problems.append(f"{label}:receipt_{field}_missing")
    if not _is_sha(identity["commit"], SHA40_RE):
        problems.append(f"{label}:receipt_commit_invalid")
    if not _is_sha(identity["tree"], SHA40_RE):
        problems.append(f"{label}:receipt_tree_invalid")
    if identity["evidence_class"] not in EVIDENCE_CLASSES:
        problems.append(f"{label}:receipt_evidence_class_invalid")
    return problems


def _reference_key(reference: Any, *, receipt_root: Path) -> str | None:
    """Return the canonical in-root path for a concrete receipt reference."""

    if not isinstance(reference, str) or not reference.strip() or reference.startswith("opaque:"):
        return None
    candidate = Path(reference.strip())
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    candidate = receipt_root / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    try:
        resolved.relative_to(receipt_root.resolve())
    except ValueError:
        return None
    return str(resolved)


def _slot_receipt_problems(
    slot_name: str,
    slot: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> list[str]:
    """Compare every claimed slot fact with the referenced receipt payload."""

    problems: list[str] = []
    problems.extend(_receipt_identity_problems(receipt, slot_name))
    identity = _receipt_identity(receipt)
    for field in ("repository", "ref", "commit", "tree", "evidence_class"):
        if identity[field] != slot.get(field):
            problems.append(f"receipt_{field}_mismatch")
    if identity["slot"] != slot_name:
        problems.append("receipt_slot_mismatch")
    packet = _receipt_value(receipt, "packet", "packet_id", "packetId")
    if packet != slot.get("packet"):
        problems.append("receipt_packet_mismatch")
    expected_environment = slot.get("environment")
    if expected_environment is not None:
        environment = _receipt_value(receipt, "environment", "environment_id", "environmentId")
        if environment != expected_environment:
            problems.append("receipt_environment_mismatch")
    command_digest = _receipt_value(
        receipt,
        "command_or_profile_digest",
        "commandOrProfileDigest",
        "command_digest",
        "commandDigest",
        "profile_digest",
        "profileDigest",
    )
    if command_digest != slot.get("command_or_profile_digest"):
        problems.append("receipt_command_or_profile_digest_mismatch")
    result_digest = _receipt_value(receipt, "result_digest", "resultDigest", "result_sha256", "resultSha256")
    if result_digest != slot.get("result_digest"):
        problems.append("receipt_result_digest_mismatch")
    return problems


def _validate_ledger(
    payload: Mapping[str, Any],
    *,
    receipt_root: Path,
    known_receipt_digests: Mapping[str, str],
    known_receipts: Mapping[str, Mapping[str, Any]],
    slot_bindings: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> tuple[list[str], dict[str, int]]:
    ledger = payload.get("ledger")
    if not isinstance(ledger, Sequence) or isinstance(ledger, (str, bytes, bytearray)) or not ledger:
        raise ReconciliationError("ledger_missing")
    counts = {classification: 0 for classification in CLASSIFICATIONS}
    problems: list[str] = []
    for index, row in enumerate(ledger):
        if not isinstance(row, Mapping):
            problems.append(f"ledger[{index}]:row_not_object")
            continue
        classification = row.get("classification")
        if classification not in CLASSIFICATIONS:
            problems.append(f"ledger[{index}]:invalid_classification")
            continue
        counts[classification] += 1
        if not isinstance(row.get("id"), str) or not row["id"].strip():
            problems.append(f"ledger[{index}]:id_missing")
        if not isinstance(row.get("basis"), str) or not row["basis"].strip():
            problems.append(f"ledger[{index}]:basis_missing")
        refs = row.get("receipt_refs")
        if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes, bytearray)) or not refs:
            problems.append(f"ledger[{index}]:receipt_refs_missing")
            refs = []
        referenced_keys: set[str] = set()
        for ref_index, reference in enumerate(refs):
            if not isinstance(reference, str) or not reference.strip():
                problems.append(f"ledger[{index}]:receipt_ref_invalid:{ref_index}")
                continue
            if reference.startswith("opaque:"):
                problems.append(f"ledger[{index}]:receipt_ref_unresolvable:{ref_index}")
                continue
            key = _reference_key(reference, receipt_root=receipt_root)
            if key is None:
                problems.append(f"ledger[{index}]:receipt_ref_unresolvable:{ref_index}")
                continue
            referenced_keys.add(key)
            digest = known_receipt_digests.get(key)
            if digest is None:
                problems.append(f"ledger[{index}]:receipt_digest_unbound:{ref_index}")
                continue
            ref_problems, _receipt, _resolved = _resolve_receipt_reference(
                reference,
                digest,
                label=f"ledger[{index}]",
                receipt_root=receipt_root,
            )
            problems.extend(f"{problem}:{ref_index}" for problem in ref_problems)

        required_classes = row.get("required_evidence_classes")
        if not isinstance(required_classes, Sequence) or isinstance(required_classes, (str, bytes, bytearray)) or not required_classes:
            problems.append(f"ledger[{index}]:required_evidence_classes_missing")
            required_classes = []
        supplied_classes = {
            str(_receipt_identity(known_receipts[key])["evidence_class"])
            for key in referenced_keys
            if key in known_receipts
        }
        for evidence_class in required_classes:
            if evidence_class not in EVIDENCE_CLASSES:
                problems.append(f"ledger[{index}]:evidence_class_invalid:{evidence_class}")
            elif evidence_class not in supplied_classes:
                problems.append(f"ledger[{index}]:evidence_class_missing:{evidence_class}")
    return problems, counts


def _validate_rollback(
    rollback: Any,
    *,
    receipt_root: Path,
) -> list[str]:
    """Require rollback receipt, identity, action, and result evidence."""

    if not isinstance(rollback, Mapping):
        return ["rollback_recovery_missing"]
    problems: list[str] = []
    for name, value in rollback.items():
        if name == "immutable_release_rule":
            continue
        label = f"rollback:{name}"
        if not isinstance(value, Mapping) or value.get("status") not in {"PROVEN", "ACCEPTED"}:
            problems.append(f"{label}:not_proven")
            continue
        for field in ("receipt_ref", "receipt_digest", "identity", "action", "result_digest"):
            if field not in value or value[field] in (None, "", {}):
                problems.append(f"{label}:{field}_missing")
        if isinstance(value.get("result_digest"), str) and not SHA256_RE.fullmatch(value["result_digest"]):
            problems.append(f"{label}:result_digest_invalid")
        identity = value.get("identity")
        if not isinstance(identity, Mapping):
            continue
        for field in ("repository", "ref", "commit", "tree"):
            if not isinstance(identity.get(field), str) or not identity[field].strip():
                problems.append(f"{label}:identity_{field}_missing")
        if not _is_sha(identity.get("commit"), SHA40_RE):
            problems.append(f"{label}:identity_commit_invalid")
        if not _is_sha(identity.get("tree"), SHA40_RE):
            problems.append(f"{label}:identity_tree_invalid")
        reference_problems, receipt, _resolved = _resolve_receipt_reference(
            value.get("receipt_ref"),
            value.get("receipt_digest"),
            label=label,
            receipt_root=receipt_root,
        )
        problems.extend(reference_problems)
        if receipt is None:
            continue
        receipt_identity = _receipt_identity(receipt)
        for field in ("repository", "ref", "commit", "tree"):
            if receipt_identity[field] != identity.get(field):
                problems.append(f"{label}:identity_mismatch")
                break
        receipt_action = _receipt_value(receipt, "action", "rollback_action", "rollbackAction")
        if receipt_action != value.get("action"):
            problems.append(f"{label}:action_mismatch")
        receipt_result = _receipt_value(receipt, "result_digest", "resultDigest", "result_sha256", "resultSha256")
        if receipt_result != value.get("result_digest"):
            problems.append(f"{label}:result_digest_mismatch")
    return problems


def reconcile(payload: Mapping[str, Any], *, receipt_root: Path | None = None) -> dict[str, Any]:
    """Return a deterministic COMPLETE/HOLD report without external I/O."""

    root = (receipt_root or Path.cwd()).resolve()
    dependency_problems, dependency_receipts, dependency_digests = _validate_dependencies(
        payload, receipt_root=root
    )
    slot_problems, slot_receipts, slot_digests, slot_bindings = _validate_slots(
        payload, receipt_root=root
    )
    known_receipt_digests = {**dependency_digests, **slot_digests}
    known_receipts = {**dependency_receipts, **slot_receipts}
    ledger_problems, counts = _validate_ledger(
        payload,
        receipt_root=root,
        known_receipt_digests=known_receipt_digests,
        known_receipts=known_receipts,
        slot_bindings=slot_bindings,
    )
    rollback_problems = _validate_rollback(payload.get("rollback_recovery"), receipt_root=root)

    blockers: list[str] = []
    if payload.get("status") == "PREPARATORY_ONLY":
        blockers.append("preparatory_only_input")
    blockers.extend(dependency_problems)
    blockers.extend(f"slot:{name}:{reason}" for name, reasons in slot_problems.items() for reason in reasons)
    blockers.extend(ledger_problems)
    blockers.extend(rollback_problems)
    if counts.get("not_proven", 0) or counts.get("partial", 0) or counts.get("blocked_external", 0):
        blockers.append("ledger_contains_unresolved_classification")
    if payload.get("decision") == "COMPLETE" and blockers:
        blockers.append("input_claims_complete_with_unresolved_evidence")
    decision = "COMPLETE" if not blockers else "HOLD"
    report = {
        "schema_version": "0.1",
        "kind": "linkskills.pkt-26.final-dod-reconciliation-result",
        "decision": decision,
        "external_io_performed": False,
        "claims": {
            "provider_live": False,
            "stage_proven": False,
            "vps_proven": False,
            "e2e_proven": False,
            "production_proven": False,
        },
        "ledger_counts": counts,
        "dependency_problems": dependency_problems,
        "slot_problems": slot_problems,
        "rollback_problems": rollback_problems,
        "blockers": sorted(set(blockers)),
    }
    report["report_sha256"] = _digest(report)
    return report


def main(argv: list[str] | None = None) -> int:
    """Evaluate a receipt JSON file; HOLD is a successful truthful evaluation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.receipt.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ReconciliationError("receipt_root_not_object")
        report = reconcile(payload, receipt_root=Path.cwd())
    except (OSError, json.JSONDecodeError, ReconciliationError) as exc:
        print(f"invalid reconciliation input: {exc}")
        return 2
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0 if report["decision"] == "COMPLETE" or not args.require_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
