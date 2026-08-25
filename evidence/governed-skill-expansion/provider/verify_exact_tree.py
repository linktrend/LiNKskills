"""Fail-closed PKT-25 exact-tree/provider verification rehearsal.

The verifier records source evidence only.  It never contacts a provider,
deploys anything, promotes a branch, or turns a preparatory receipt into an
admission.  The PKT-24 dependency is intentionally unresolved until the
serially integrated catalogue candidate is supplied by its owning lane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKET = "PKT-25"
PREPARATORY_ONLY = "PREPARATORY_ONLY"
BASE_COMMIT = "21271dffa4ab3a63ee16d0d9a6ce2011f069cf1a"
BASE_TREE = "e0ad65a3643d1fdfb1b5df7e2ba6935e67f2fa9e"
OWNED_PREFIX = "evidence/governed-skill-expansion/provider/"
GENERATED_OUTPUT_EXCEPTION = ".github/linktrend-secret-scan-fixtures.json"
PKT24_DEPENDENCY = {
    "packet": "PKT-24",
    "status": "unresolved",
    "required_for": "serially integrated catalogue, migration, and authoritative-document candidate",
    "effect": "no exact provider-source admission or selectable/live claim",
}

CHECK_DEFINITIONS: dict[str, dict[str, Any]] = {
    "scoped_packet_checks": {
        "label": "focused packet checks and negative probes",
        "commands": ["python3 -m unittest discover -s tests -p 'test_*.py' -v"],
    },
    "full_repository_validation": {
        "label": "repository-wide validation",
        "commands": ["python3 -m unittest discover -s tests -p 'test_*.py' -v"],
    },
    "catalog_check": {
        "label": "catalogue generation/check",
        "commands": ["python3 scripts/build-catalog-index.py --check"],
    },
    "isolated_package_tests": {
        "label": "isolated package tests",
        "commands": ["python3 -m unittest discover -s packages -p 'test_*.py' -v"],
    },
    "secret_scan": {
        "label": "secret scan",
        "commands": ["python3 scripts/gitops/secret_scan.py --repo-root ."],
    },
    "privacy_scan": {
        "label": "privacy and raw-data negative checks",
        "commands": ["python3 -m unittest discover -s tests -p 'test_*privacy*.py' -v"],
    },
    "exact_diff_audit": {
        "label": "exact base-to-candidate diff audit",
        "commands": ["git diff --check", "git diff --name-only <base-commit>..<candidate-commit>"],
    },
    "ancestry_audit": {
        "label": "issue-commit ancestry audit",
        "commands": ["git merge-base --is-ancestor <issue-commit> <candidate-commit>"],
    },
}

_HEX_RE = re.compile(r"^[0-9a-f]{40}$")
_REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


class VerificationError(ValueError):
    """Raised when a verification input is malformed rather than failed."""


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _sha(value: Any) -> bool:
    return bool(_HEX_RE.fullmatch(_text(value)))


def normalize_origin(value: Any) -> str:
    """Normalize an origin for exact comparison without hiding its host."""

    origin = _text(value)
    if not origin or any(character.isspace() for character in origin):
        raise VerificationError("origin_must_be_nonempty_and_whitespace_free")
    if "@" in origin.split("//", 1)[-1].split("/", 1)[0] and not origin.startswith("git@"):
        raise VerificationError("origin_must_not_contain_credentials")
    if origin.startswith("git@") and ":" in origin:
        host, path = origin[4:].split(":", 1)
        origin = f"ssh://{host}/{path}"
    if origin.endswith("/"):
        origin = origin[:-1]
    if origin.endswith(".git"):
        origin = origin[:-4]
    if "://" in origin:
        scheme, remainder = origin.split("://", 1)
        origin = f"{scheme.lower()}://{remainder}"
    if "/" not in origin.split("://", 1)[-1]:
        raise VerificationError("origin_must_include_repository_path")
    return origin


def normalize_ref(value: Any) -> str:
    """Normalize a Git ref while rejecting symbolic or ambiguous refs."""

    ref = _text(value)
    if not ref or not _REF_RE.fullmatch(ref) or ref in {"HEAD", "FETCH_HEAD"}:
        raise VerificationError("ref_must_be_an_explicit_git_ref")
    if ref.startswith("refs/"):
        return ref
    return f"refs/heads/{ref}"


def _check(expected: Any, observed: Any, reason: str, *, normalize=None) -> dict[str, Any]:
    if expected in (None, ""):
        return {"status": "HOLD", "reason": f"expected_{reason}_missing", "observed": observed}
    expected_value = normalize(expected) if normalize else expected
    observed_value = normalize(observed) if normalize else observed
    if expected_value != observed_value:
        return {
            "status": "FAIL",
            "reason": f"{reason}_mismatch",
            "expected": expected_value,
            "observed": observed_value,
        }
    return {"status": "PASS", "reason": f"{reason}_exact", "value": observed_value}


def verify_checkout_identity(
    observed: Mapping[str, Any],
    expected: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify normalized origin/ref/commit/tree and a clean checkout."""

    expected = expected or {}
    origin = normalize_origin(observed.get("origin"))
    ref = normalize_ref(observed.get("ref"))
    commit = _text(observed.get("commit"))
    tree = _text(observed.get("tree"))
    if not _sha(commit) or not _sha(tree):
        raise VerificationError("checkout_commit_and_tree_must_be_lowercase_sha")
    checks = {
        "origin": _check(expected.get("origin"), origin, "origin", normalize=normalize_origin),
        "ref": _check(expected.get("ref"), ref, "ref", normalize=normalize_ref),
        "commit": _check(expected.get("commit"), commit, "commit"),
        "tree": _check(expected.get("tree"), tree, "tree"),
        "clean": {
            "status": "PASS" if observed.get("clean") is True else "FAIL",
            "reason": "clean_checkout" if observed.get("clean") is True else "dirty_checkout",
            "observed": observed.get("clean"),
        },
    }
    return {"observed": {"origin": origin, "ref": ref, "commit": commit, "tree": tree, "clean": observed.get("clean")}, "checks": checks}


def verify_provider_source(identity: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate provider source identity without asserting provider availability."""

    identity = identity or {}
    fields = {key: _text(identity.get(key)) for key in ("repository", "ref", "commit", "tree")}
    paths = identity.get("paths")
    valid_paths = bool(paths) and isinstance(paths, Sequence) and not isinstance(paths, (str, bytes, bytearray)) and all(
        _text(path).startswith(OWNED_PREFIX) for path in paths
    )
    reasons = []
    if not all(fields.values()):
        reasons.append("provider_source_identity_missing")
    if fields["ref"]:
        try:
            normalize_ref(fields["ref"])
        except VerificationError:
            reasons.append("provider_source_ref_invalid")
    if fields["commit"] and not _sha(fields["commit"]):
        reasons.append("provider_source_commit_invalid")
    if fields["tree"] and not _sha(fields["tree"]):
        reasons.append("provider_source_tree_invalid")
    if not valid_paths:
        reasons.append("provider_source_paths_missing_or_out_of_scope")
    return {
        "status": "PASS" if not reasons else "HOLD",
        "identity": {**fields, "paths": list(paths) if valid_paths else []},
        "reason_codes": sorted(set(reasons)),
    }


def verify_scope(changed_paths: Sequence[str] | None) -> dict[str, Any]:
    """Reject paths outside provider scope except the generated scan fixture."""

    paths = sorted({_text(path) for path in (changed_paths or []) if _text(path)})
    outside = [path for path in paths if not path.startswith(OWNED_PREFIX) and path != GENERATED_OUTPUT_EXCEPTION]
    return {
        "status": "PASS" if not outside else "FAIL",
        "allowed_prefix": OWNED_PREFIX,
        "generated_output_exceptions": [GENERATED_OUTPUT_EXCEPTION],
        "changed_paths": paths,
        "outside_owned_paths": outside,
        "reason": "owned_paths_only" if not outside else "owned_path_leak",
    }


def _check_statuses(check_statuses: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    supplied = check_statuses or {}
    unknown = sorted(set(supplied) - set(CHECK_DEFINITIONS))
    if unknown:
        raise VerificationError("unknown_check_names:" + ",".join(unknown))
    return {
        name: {
            "status": _text(supplied.get(name)) or "NOT_RUN",
            "label": definition["label"],
            "commands": list(definition["commands"]),
        }
        for name, definition in CHECK_DEFINITIONS.items()
    }


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def make_receipt(
    checkout: Mapping[str, Any],
    *,
    expected_checkout: Mapping[str, Any] | None = None,
    provider_source: Mapping[str, Any] | None = None,
    changed_paths: Sequence[str] | None = None,
    check_statuses: Mapping[str, Any] | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic preparatory receipt; admission is always false."""

    checkout_result = verify_checkout_identity(checkout, expected_checkout)
    provider_result = verify_provider_source(provider_source)
    scope_result = verify_scope(changed_paths)
    checks = _check_statuses(check_statuses)
    all_checks_pass = all(item["status"] == "PASS" for item in checks.values())
    reasons = [
        "dependency_pkt24_unresolved",
        "preparatory_only_receipt",
    ]
    if provider_result["status"] != "PASS":
        reasons.extend(provider_result["reason_codes"])
    if scope_result["status"] != "PASS":
        reasons.append("owned_path_leak")
    if not all_checks_pass:
        reasons.append("verification_checks_not_all_pass")
    receipt: dict[str, Any] = {
        "schema_version": "0.1",
        "packet": PACKET,
        "status": PREPARATORY_ONLY,
        "route": {
            "route_id": "codex-luna-high",
            "model": "Codex Luna",
            "reasoning_effort": "high",
            "recorded_at": recorded_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "baseline": {"commit": BASE_COMMIT, "tree": BASE_TREE, "ref": "refs/remotes/origin/development"},
        "dependency": dict(PKT24_DEPENDENCY),
        "checkout": checkout_result,
        "provider_source": provider_result,
        "scope": scope_result,
        "verification": {"checks": checks, "all_checks_pass": all_checks_pass},
        "claims": {
            "exact_source_candidate_passed": False,
            "provider_live": False,
            "stage_proven": False,
            "vps_proven": False,
            "production_proven": False,
        },
        "admission": {"admissible": False, "reason_codes": sorted(set(reasons))},
    }
    receipt["receipt_digest"] = _digest(receipt)
    return receipt


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def read_checkout(repo_root: Path) -> dict[str, Any]:
    """Read local Git identity for a later exact candidate run."""

    status = _git(repo_root, "status", "--porcelain=v1")
    upstream = _git(repo_root, "rev-parse", "--symbolic-full-name", "--verify", "@{upstream}")
    return {
        "origin": _git(repo_root, "remote", "get-url", "origin"),
        "ref": upstream,
        "commit": _git(repo_root, "rev-parse", "HEAD"),
        "tree": _git(repo_root, "rev-parse", "HEAD^{tree}"),
        "clean": not bool(status),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-tree")
    parser.add_argument("--expected-ref")
    parser.add_argument("--expected-origin")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    checkout = read_checkout(args.repo_root)
    expected = {
        "origin": args.expected_origin,
        "ref": args.expected_ref,
        "commit": args.expected_commit,
        "tree": args.expected_tree,
    }
    changed = _git(args.repo_root, "diff", "--name-only", BASE_COMMIT, "HEAD").splitlines()
    receipt = make_receipt(checkout, expected_checkout=expected, changed_paths=changed)
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if receipt["admission"]["admissible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
