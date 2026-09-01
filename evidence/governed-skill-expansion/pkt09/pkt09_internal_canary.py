#!/usr/bin/env python3
"""Source-only PKT-09 internal synthetic canary execution.

This helper reuses already-landed Operational Reporting artifacts and the
current packet ledger. It does not re-implement PKT-09, mutate eligibility,
activate a consumer, contact a provider, or run a broad Full suite.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


PACKET = "PKT-09"
LEDGER_CANDIDATE_COMMIT = "5c091a75c364a723e5364f883898fa26da6dc491"
LEDGER_CANDIDATE_TREE = "ac57fbee285851e32f420b0bd48c61bffc59b657"
EXPECTED_ORIGIN = "https://github.com/linktrend/LiNKskills"
PROTECTED_BASE_REF = "refs/remotes/origin/development"
FALSE_CLAIMS = (
    "activation",
    "consumer",
    "current_pointer",
    "e2e",
    "hosted_stage",
    "ordinary_selectability",
    "production",
    "provider_live",
    "qualification_admission",
    "vps",
)
OWNED_SOURCE_PATHS = (
    "skills/operational-reporting",
    "skills/executive-sync-8am",
    "skills/studio-health-reporting",
    "tests/skills/operational_reporting",
)
ALLOWED_CHANGED_PATH_PREFIXES = (
    "docs/handoffs/2026-08-31-issue-310-pkt09-internal-synthetic-canary.md",
    "evidence/governed-skill-expansion/pkt09/",
    "tests/integrations/test_pkt09_internal_canary.py",
)
FOCUSED_COMMANDS = (
    ("validator", ["python3", "validator.py", "--repo-root", ".", "--path", "skills/operational-reporting"]),
    ("pkt09_contracts", ["python3", "-m", "unittest", "discover", "-s", "tests/skills/operational_reporting", "-v"]),
    (
        "current_packet_ledger",
        ["python3", "evidence/governed-skill-expansion/test_current_packet_ledger.py"],
    ),
)


class Pkt09CanaryError(ValueError):
    """Raised when the PKT-09 synthetic canary cannot be admitted."""


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sanitize_origin(value: Any) -> str:
    """Strip credentials from a Git origin so receipts never store tokens."""

    origin = _text(value)
    if not origin:
        raise Pkt09CanaryError("origin_must_be_nonempty")
    if origin.startswith("git@") and ":" in origin[4:]:
        host, path = origin[4:].split(":", 1)
        origin = f"https://{host}/{path}"
    parsed = urlsplit(origin)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        origin = f"{parsed.scheme}://{parsed.hostname}{parsed.path}"
    origin = origin.rstrip("/")
    if origin.endswith(".git"):
        origin = origin[:-4]
    return origin


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise Pkt09CanaryError(f"json_object_required:{path}")
    return dict(payload)


def ledger_path(repo_root: Path) -> Path:
    return repo_root / "evidence" / "governed-skill-expansion" / "current-packet-ledger.json"


def classify_seed_path(repo_root: Path) -> Path:
    return repo_root / "evidence" / "initial-skill-seed" / "member-classification.json"


def publication_path(repo_root: Path) -> Path:
    return repo_root / "evidence" / "initial-skill-seed" / "canary-publication-receipt.json"


def pkt22_path(repo_root: Path) -> Path:
    return repo_root / "role-packs" / "pkt-22-source-receipt.json"


def verify_ledger_candidate(repo_root: Path) -> dict[str, Any]:
    """Confirm the named ledger candidate is present and names PKT-09."""

    commit = _git(repo_root, "rev-parse", LEDGER_CANDIDATE_COMMIT)
    tree = _git(repo_root, "rev-parse", f"{LEDGER_CANDIDATE_COMMIT}^{{tree}}")
    if commit != LEDGER_CANDIDATE_COMMIT or tree != LEDGER_CANDIDATE_TREE:
        raise Pkt09CanaryError("ledger_candidate_identity_mismatch")
    ancestor = subprocess.call(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", LEDGER_CANDIDATE_COMMIT, "HEAD"],
    )
    if ancestor != 0:
        raise Pkt09CanaryError("ledger_candidate_must_be_ancestor_of_head")
    return {
        "commit": commit,
        "protected": True,
        "reason": "named_phase_candidate_landed_on_development_do_not_mutate",
        "tree": tree,
    }


def verify_source_unmutated(repo_root: Path, base: str) -> list[str]:
    """Return owned PKT-09 source paths that differ from the protected base."""

    changed = _git(repo_root, "diff", "--name-only", f"{base}..HEAD").splitlines()
    owned = [
        path
        for path in changed
        if any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in OWNED_SOURCE_PATHS)
    ]
    if owned:
        raise Pkt09CanaryError("pkt09_source_must_not_be_reimplemented:" + ",".join(owned))
    return owned


def verify_changed_paths_are_canary_only(changed_paths: Sequence[str]) -> list[str]:
    """Admit only evidence, focused tests, and the issue handoff."""

    normalized = []
    for value in changed_paths:
        path = _text(value)
        if not path or path.startswith("/") or ".." in path.split("/"):
            raise Pkt09CanaryError("changed_paths_must_be_relative_repo_paths")
        if not any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_CHANGED_PATH_PREFIXES):
            raise Pkt09CanaryError("changed_path_outside_pkt09_canary_lane:" + path)
        normalized.append(path)
    return sorted(set(normalized))


def inspect_global_eligibility(repo_root: Path) -> dict[str, Any]:
    """Keep all 207 overlay members globally ineligible."""

    seed = load_json(classify_seed_path(repo_root))
    members = seed.get("members")
    if not isinstance(members, list) or len(members) != 207:
        raise Pkt09CanaryError("expected_207_classified_members")
    selectable = [item["release_id"] for item in members if item.get("ordinary_selectable")]
    qualified = [item["release_id"] for item in members if item.get("stable_qualified")]
    ineligible = 0
    for collection in repo_root.glob("collections/*/eligibility/*-ineligible.json"):
        payload = load_json(collection)
        if payload.get("decision") != "ineligible":
            raise Pkt09CanaryError("eligibility_decision_must_remain_ineligible:" + collection.name)
        activation = payload.get("consumer_profile_activation")
        if not isinstance(activation, Mapping) or activation.get("status") is not False:
            raise Pkt09CanaryError("consumer_profile_activation_must_remain_false:" + collection.name)
        ineligible += 1
    if ineligible != 207:
        raise Pkt09CanaryError("expected_207_ineligible_eligibility_records")
    if selectable or qualified:
        raise Pkt09CanaryError("overlay_members_must_remain_nonselectable_and_unqualified")
    counts = seed.get("summary", {}).get("counts") if isinstance(seed.get("summary"), Mapping) else {}
    return {
        "approved_internal_canary": int(counts.get("approved_internal_canary") or 0),
        "ineligible_count": ineligible,
        "member_count": 207,
        "needs_correction": int(counts.get("needs_correction") or 0),
        "needs_focused_review": int(counts.get("needs_focused_review") or 0),
        "ordinary_selectable_count": 0,
        "stable_qualified_count": 0,
        "superseded": int(counts.get("superseded") or 0),
    }


def inspect_consumer_and_live_holds(repo_root: Path) -> dict[str, Any]:
    """Copy consumer/provider/live HOLDs; never upgrade them."""

    publication = load_json(publication_path(repo_root))
    pkt22 = load_json(pkt22_path(repo_root))
    activations = []
    for path in sorted((repo_root / "configs" / "consumer-activation").glob("*-internal-canary.json")):
        manifest = load_json(path)
        enabled = manifest.get("activation", {}).get("enabled")
        if enabled is not False or manifest.get("live_apply") is not False:
            raise Pkt09CanaryError("consumer_activation_must_remain_disabled:" + path.name)
        activations.append(path.name)
    if publication.get("consumer_activation") or publication.get("live_provider_publication") or publication.get("current_pointer_changed"):
        raise Pkt09CanaryError("publication_receipt_holds_must_remain_false")
    if pkt22.get("status") != "HOLD" or pkt22.get("admitted") is not False:
        raise Pkt09CanaryError("pkt22_must_remain_hold")
    claims = {key: False for key in FALSE_CLAIMS}
    return {
        "consumer_activation_manifests": activations,
        "pkt22_status": "HOLD",
        "publication_consumer_activation": False,
        "publication_current_pointer_changed": False,
        "publication_live_provider": False,
        **{f"claim_{key}": False for key in FALSE_CLAIMS},
        "claims": claims,
    }


def inspect_ledger_admission(repo_root: Path) -> dict[str, Any]:
    """Admit only PKT-09 as the first dependency-ready internal canary."""

    ledger = load_json(ledger_path(repo_root))
    first = ledger.get("first_dependency_ready_internal_canary")
    if not isinstance(first, Mapping):
        raise Pkt09CanaryError("missing_first_dependency_ready_internal_canary")
    if first.get("packet_id") != PACKET:
        raise Pkt09CanaryError("first_internal_canary_must_be_pkt_09")
    if first.get("implementation_status") != "SOURCE_LANDED_DO_NOT_DUPLICATE":
        raise Pkt09CanaryError("pkt09_must_remain_source_landed_do_not_duplicate")
    if first.get("next_authorized_skills_mutation") != "none":
        raise Pkt09CanaryError("skills_product_mutation_is_not_authorized")
    packets = {row["id"]: row for row in ledger.get("packets") or [] if isinstance(row, Mapping) and row.get("id")}
    pkt09 = packets.get(PACKET)
    if not isinstance(pkt09, Mapping) or pkt09.get("dependency_ready") is not True:
        raise Pkt09CanaryError("pkt09_is_not_dependency_ready")
    if pkt09.get("source_classification") != "SOURCE_LANDED":
        raise Pkt09CanaryError("pkt09_source_classification_mismatch")
    if ledger.get("decision") != "HOLD" or ledger.get("completion_claimed") is not False:
        raise Pkt09CanaryError("ledger_decision_must_remain_hold")
    for key in FALSE_CLAIMS:
        if ledger.get("claims", {}).get(key) is not False:
            raise Pkt09CanaryError("ledger_claim_must_remain_false:" + key)
    return {
        "decision": "HOLD",
        "first_packet": PACKET,
        "implementation_status": first["implementation_status"],
        "wave": first.get("wave"),
    }


def run_focused_checks(repo_root: Path) -> list[dict[str, Any]]:
    """Run named PKT-09 and ledger reuse checks only."""

    results = []
    for name, command in FOCUSED_COMMANDS:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        passed = completed.returncode == 0
        if name == "validator" and "Validation passed" not in completed.stdout:
            passed = False
        if not passed:
            raise Pkt09CanaryError(f"focused_check_failed:{name}:{completed.returncode}")
        results.append(
            {
                "command": command,
                "name": name,
                "returncode": completed.returncode,
                "status": "PASS",
            }
        )
    return results


def bind_internal_canary_receipt(
    repo_root: Path,
    *,
    run_checks: bool = True,
) -> dict[str, Any]:
    """Bind a source-only PKT-09 synthetic canary receipt to this checkout."""

    repo_root = repo_root.resolve()
    origin = sanitize_origin(_git(repo_root, "remote", "get-url", "origin"))
    if origin != EXPECTED_ORIGIN:
        raise Pkt09CanaryError("origin_must_be_linkskills")
    head = _git(repo_root, "rev-parse", "HEAD")
    tree = _git(repo_root, "rev-parse", "HEAD^{tree}")
    ref = _git(repo_root, "symbolic-ref", "--quiet", "HEAD")
    development = _git(repo_root, "rev-parse", PROTECTED_BASE_REF)
    ledger_candidate = verify_ledger_candidate(repo_root)
    admission = inspect_ledger_admission(repo_root)
    eligibility = inspect_global_eligibility(repo_root)
    holds = inspect_consumer_and_live_holds(repo_root)
    verify_source_unmutated(repo_root, development)
    changed = _git(repo_root, "diff", "--name-only", f"{development}..HEAD").splitlines()
    if changed:
        verify_changed_paths_are_canary_only(changed)
    checks = run_focused_checks(repo_root) if run_checks else []
    receipt = {
        "admitted_packets": [PACKET],
        "broad_full_suite": False,
        "candidate": {
            "commit": head,
            "origin": origin,
            "ref": ref,
            "tree": tree,
        },
        "claims": holds["claims"],
        "completion_claimed": False,
        "decision": "HOLD",
        "development_head": development,
        "eligibility": eligibility,
        "executor": {
            "one_executor_per_packet": True,
            "packet_id": PACKET,
            "packet_title": "Operational Reporting skill family",
        },
        "focused_checks": checks,
        "implementation_status": "SOURCE_LANDED_DO_NOT_DUPLICATE",
        "kind": "linkskills.internal-synthetic-canary-execution",
        "ledger_admission": admission,
        "ledger_candidate": ledger_candidate,
        "live_vps_staging_main_production": False,
        "packet": PACKET,
        "proof_scope": "source_synthetic",
        "schema_version": "0.1",
        "skill_source_reimplemented": False,
        "status": "INTERNAL_SYNTHETIC_CANARY_HOLD",
        "wave": 2,
    }
    receipt["receipt_digest"] = _canonical_digest({key: value for key, value in receipt.items() if key != "receipt_digest"})
    return receipt


def write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    """Write a canonical receipt JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    receipt = bind_internal_canary_receipt(repo_root)
    target = Path(__file__).with_name("internal-synthetic-canary-receipt.json")
    write_receipt(target, receipt)
    print(json.dumps({"receipt": str(target), "digest": receipt["receipt_digest"], "commit": receipt["candidate"]["commit"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
