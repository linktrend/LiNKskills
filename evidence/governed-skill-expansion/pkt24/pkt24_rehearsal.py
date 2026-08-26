"""Fail-closed PKT-24 packaging and offline rehearsal helpers.

This module is intentionally source-local.  It validates the migration package,
reference-only consumer configuration, and redacted loopback fixture without
contacting a provider, database, consumer, host, or deployment endpoint.  The
receipt binder records exact Git identity and digests but always remains
``PREPARATORY_ONLY`` while PKT-22/23 and external evidence are unresolved.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


PACKET = "PKT-24"
PREPARATORY_ONLY = "PREPARATORY_ONLY"
EXPECTED_ORIGIN = "https://github.com/linktrend/LiNKskills"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TREE_RE = COMMIT_RE
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PROTECTED_BASE_REF = "refs/remotes/origin/development"
ALLOWED_CHANGED_PATH_PREFIXES = (
    ".github/linktrend-secret-scan-fixtures.json",
    "configs/pkt24/",
    "docs/integrations/PKT-24-REMAINING-DOD.md",
    "evidence/governed-skill-expansion/pkt24/",
    "evidence/governed-skill-expansion/provider/",
    "evidence/governed-skill-expansion/final/",
    "tests/integrations/test_pkt24_remaining_dod.py",
)

DEPENDENCY_HOLDS = [
    "PKT-22 unresolved",
    "PKT-23 unresolved",
    "PKT-03/ISS-03 dependency for migration 000012 unresolved",
    "LiNKplatform live migration/auth receipts absent",
    "OpenClaw consumer proof absent",
    "LiNKautowork receipt absent",
    "VPS/deployment receipt absent",
    "independent final verification absent",
]

# The order is the source-owned apply order.  This is a manifest, not an apply
# command: only LiNKplatform may apply migrations in a named environment.
MIGRATION_MANIFEST: tuple[dict[str, Any], ...] = (
    {"order": 2, "up": "20260715_000002_lskills_catalog_core.sql", "sha256": "4991dd628cc501a1013a4d7c3d8f859274e62ff847e768f106b0e3c2b89d8414", "down": None},
    {"order": 3, "up": "20260715_000003_lskills_catalog_seed.sql", "sha256": "5e8f58a7159ad09f0c6389e12060c6a9cc76ff73dcfc2397ddea256d47a75e82", "down": None},
    {"order": 4, "up": "20260718_000004_lskills_postgrest_exposure.sql", "sha256": "4220d70b626313f572a38720958fb78550b3b89c0efab5366a449d33c0b22ca0", "down": None},
    {"order": 5, "up": "20260727_000005_lskills_registry_foundation.sql", "sha256": "36081765032f21dfd2dcca223035555e1e54b71298874235def8e0362c55c4ed", "down": None},
    {"order": 6, "up": "20260728_000006_lskills_rls_actor_org_scope.sql", "sha256": "12c2e45e94fd9216a5857ce53ce299a953dc2ee869f89bcdb392857133df763d", "down": None},
    {"order": 7, "up": "20260730_000007_lskills_gateway_persistence.sql", "sha256": "c26d1c55d9f87e242fe1e225fd4240cd911a5e0315d88500417d491689596222", "down": None},
    {"order": 8, "up": "20260730_000008_lskills_review_queue.sql", "sha256": "0d5cf1f6abf62bddffc2e494bd8fb7faabe5aceb44266d446bb71f1209f43bab", "down": None},
    {"order": 9, "up": "20260730_000009_lskills_review_queue_actor_isolation.sql", "sha256": "acd0a1dbf81697d4e278ed4cdfa11d4b410b383420e02e6105940f578b6b6467", "down": None},
    {"order": 10, "up": "20260803_000010_lskills_canary_echo_usable_seed.sql", "sha256": "5e391f4845984dbf83724b3ac931a879f774f91014fb46ced89154145df9f059", "down": "20260803_000010_lskills_canary_echo_usable_seed_down.sql", "down_sha256": "3b48c7f284ae902d6dd97d86dee5f7ba222d04d7900335bd3b3abb9681a2ef5e"},
    {"order": 11, "up": "20260804_000011_lskills_gateway_role_rls_contract.sql", "sha256": "0a8c56ee8ac2b3368d2a0ea8f6cc98719ccbc852d884dc34bc0143d5c7984a73", "down": "20260804_000011_lskills_gateway_role_rls_contract_down.sql", "down_sha256": "b538241ef3c95af5e1f51a4781c7600644365720343016d41f15a935e209af89"},
    {"order": 12, "up": "20260824_000012_lskills_external_collection_lifecycle.sql", "sha256": "51236e86c938e7bad8717f94949ccef4bd6ff1d4d1903796abccfbde9f819515", "down": "20260824_000012_lskills_external_collection_lifecycle_down.sql", "down_sha256": "68090475b40675d2597e28a28733cb439828a6e69c1346bf5c69731eb88ff343"},
)


class Pkt24RehearsalError(ValueError):
    """Raised when a PKT-24 package or receipt is unsafe or unbound."""


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
    """Normalize an origin and strip credentials so receipts never store tokens."""

    origin = _text(value)
    if not origin or any(character.isspace() for character in origin):
        raise Pkt24RehearsalError("origin_must_be_nonempty_and_whitespace_free")
    if origin.startswith("git@") and ":" in origin[4:]:
        host, path = origin[4:].split(":", 1)
        origin = f"ssh://{host}/{path}"
    if "://" in origin:
        scheme, remainder = origin.split("://", 1)
        slash = remainder.find("/")
        authority = remainder if slash < 0 else remainder[:slash]
        path = "" if slash < 0 else remainder[slash:]
        if "@" in authority:
            authority = authority.rsplit("@", 1)[1]
        origin = f"{scheme.lower()}://{authority}{path}"
    origin = origin.rstrip("/")
    if origin.endswith(".git"):
        origin = origin[:-4]
    if "/" not in origin.split("://", 1)[-1]:
        raise Pkt24RehearsalError("origin_must_include_repository_path")
    return origin


def _explicit_ref(value: Any) -> str:
    ref = _text(value)
    if not ref or ref in {"HEAD", "FETCH_HEAD"} or any(c.isspace() for c in ref):
        raise Pkt24RehearsalError("candidate_ref_must_be_explicit_and_non_symbolic")
    if not ref.startswith("refs/"):
        raise Pkt24RehearsalError("candidate_ref_must_use_full_refs_namespace")
    return ref


def read_physical_checkout_ref(repo_root: Path) -> str:
    """Return the fully-qualified HEAD ref from the physical checkout."""

    try:
        ref = _git(repo_root, "symbolic-ref", "--quiet", "HEAD")
    except subprocess.CalledProcessError as exc:
        raise Pkt24RehearsalError("detached_head_has_no_qualified_ref") from exc
    return _explicit_ref(ref)


def _normalized_paths(paths: Sequence[str]) -> list[str]:
    """Normalize and reject unsafe changed-path claims."""

    normalized: list[str] = []
    for value in paths:
        path = _text(value)
        if not path or path.startswith("/") or "\\" in path or ".." in path.split("/"):
            raise Pkt24RehearsalError("changed_paths_must_be_relative_repo_paths")
        normalized.append(path)
    if len(normalized) != len(set(normalized)):
        raise Pkt24RehearsalError("changed_paths_must_be_unique")
    return sorted(normalized)


def _is_allowed_path(path: str) -> bool:
    exact = {
        ".github/linktrend-secret-scan-fixtures.json",
        "docs/integrations/PKT-24-PRE-VPS-RECEIPT.json",
        "docs/integrations/PKT-24-REMAINING-DOD.md",
        "tests/integrations/test_pkt24_remaining_dod.py",
    }
    directories = (
        "configs/pkt24/",
        "evidence/governed-skill-expansion/pkt24/",
        "evidence/governed-skill-expansion/provider/",
        "evidence/governed-skill-expansion/final/",
    )
    return path in exact or path.startswith(directories)


def _resolve_identity(repo_root: Path, ref: str) -> tuple[str, str]:
    """Resolve an explicit ref to its commit and tree identities."""

    try:
        commit = _git(repo_root, "rev-parse", f"{ref}^{{commit}}")
        tree = _git(repo_root, "rev-parse", f"{ref}^{{tree}}")
    except subprocess.CalledProcessError as exc:
        raise Pkt24RehearsalError("git_ref_must_resolve") from exc
    if not COMMIT_RE.fullmatch(commit) or not TREE_RE.fullmatch(tree):
        raise Pkt24RehearsalError("git_identity_malformed")
    return commit, tree


def validate_migration_manifest(repo_root: Path) -> dict[str, Any]:
    """Validate source SQL bytes and companion down-file relationships."""

    migration_root = repo_root / "supabase" / "migrations"
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for entry in MIGRATION_MANIFEST:
        up_path = migration_root / entry["up"]
        if not up_path.is_file():
            errors.append(f"missing_up:{entry['up']}")
            continue
        observed = hashlib.sha256(up_path.read_bytes()).hexdigest()
        row = {**entry, "observed_sha256": observed, "status": "PASS" if observed == entry["sha256"] else "FAIL"}
        if observed != entry["sha256"]:
            errors.append(f"up_hash_mismatch:{entry['up']}")
        if entry["down"]:
            down_path = migration_root / entry["down"]
            if not down_path.is_file():
                errors.append(f"missing_down:{entry['down']}")
                row["down_status"] = "FAIL"
            else:
                observed_down = hashlib.sha256(down_path.read_bytes()).hexdigest()
                row["down_sha256_observed"] = observed_down
                row["down_status"] = "PASS" if observed_down == entry.get("down_sha256") else "FAIL"
                if observed_down != entry.get("down_sha256"):
                    errors.append(f"down_hash_mismatch:{entry['down']}")
        else:
            row["down_status"] = "NOT_SUPPLIED"
        rows.append(row)
    return {"status": "PASS" if not errors else "HOLD", "rows_checked": len(rows), "rows": rows, "errors": errors}


def validate_local_fixture(config: Mapping[str, Any], fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Validate that an offline rehearsal cannot address live systems."""

    errors: list[str] = []
    if _text(config.get("mode")) != "local-test":
        errors.append("mode_must_be_local-test")
    if config.get("live_enabled") is not False:
        errors.append("live_enabled_must_be_false")
    if config.get("activation_allowed") is not False:
        errors.append("activation_allowed_must_be_false")
    if config.get("provider_contacted") is not False:
        errors.append("provider_contacted_must_be_false")
    gateway_url = _text(config.get("gateway_url"))
    try:
        parsed_gateway = urlsplit(gateway_url)
        gateway_host = (parsed_gateway.hostname or "").lower()
        gateway_port = parsed_gateway.port
    except ValueError:
        parsed_gateway = None
        gateway_host = ""
        gateway_port = None
    if (
        parsed_gateway is None
        or parsed_gateway.scheme != "http"
        or gateway_host not in LOOPBACK_HOSTS
        or gateway_port is None
        or parsed_gateway.username is not None
        or parsed_gateway.password is not None
        or parsed_gateway.path not in ("", "/")
        or parsed_gateway.query
        or parsed_gateway.fragment
    ):
        errors.append("gateway_url_must_be_loopback_http")
    credential_file = _text(config.get("credential_file"))
    if not re.fullmatch(r"<[A-Za-z0-9._:-]+>", credential_file):
        errors.append("credential_file_must_remain_placeholder")
    if _text(fixture.get("fixture_class")) != "synthetic_redacted_loopback":
        errors.append("fixture_class_must_be_synthetic_redacted_loopback")
    if fixture.get("contains_private_data") is not False:
        errors.append("fixture_must_declare_no_private_data")
    events = fixture.get("events")
    event_ids: list[str] = []
    if not isinstance(events, list) or not events:
        errors.append("fixture_events_must_have_stable_ids")
    else:
        for item in events:
            event_id = _text(item.get("event_id")) if isinstance(item, Mapping) else ""
            event_ids.append(event_id)
        if any(not event_id for event_id in event_ids) or len(set(event_ids)) != len(event_ids):
            errors.append("fixture_events_must_have_stable_ids")
    return {"status": "PASS" if not errors else "HOLD", "errors": errors, "fixture_digest": _canonical_digest(fixture)}


def bind_preparatory_receipt(
    repo_root: Path,
    *,
    candidate_ref: str,
    base_commit: str,
    changed_paths: Sequence[str],
    config_digest: str,
    fixture_digest: str,
    migration_digest: str,
) -> dict[str, Any]:
    """Bind a non-admitting receipt to exact Git and package identities."""

    ref = _explicit_ref(candidate_ref)
    supplied_base = _text(base_commit)
    if supplied_base and not COMMIT_RE.fullmatch(supplied_base):
        raise Pkt24RehearsalError("base_commit_must_be_40_lowercase_hex")
    derived_base, base_tree = _resolve_identity(repo_root, PROTECTED_BASE_REF)
    if supplied_base and supplied_base != derived_base:
        raise Pkt24RehearsalError("base_commit_mismatch")
    commit, tree = _resolve_identity(repo_root, ref)
    physical_commit = _git(repo_root, "rev-parse", "HEAD")
    physical_tree = _git(repo_root, "rev-parse", "HEAD^{tree}")
    if physical_commit != commit or physical_tree != tree:
        raise Pkt24RehearsalError("candidate_must_match_physical_checkout")
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", derived_base, commit],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise Pkt24RehearsalError("candidate_must_descend_from_protected_base") from exc
    normalized_origin = sanitize_origin(_git(repo_root, "config", "--get", "remote.origin.url"))
    if normalized_origin != EXPECTED_ORIGIN:
        raise Pkt24RehearsalError("origin_mismatch")
    if _git(repo_root, "status", "--porcelain"):
        raise Pkt24RehearsalError("checkout_must_be_clean")
    supplied_paths = _normalized_paths(changed_paths)
    derived_paths = _normalized_paths(_git(repo_root, "diff", "--name-only", f"{derived_base}..{commit}").splitlines())
    if supplied_paths != derived_paths:
        raise Pkt24RehearsalError("changed_paths_mismatch_git_diff")
    outside = [path for path in derived_paths if not _is_allowed_path(path)]
    if outside:
        raise Pkt24RehearsalError("changed_paths_outside_owned_scope")
    for name, value in (("config_digest", config_digest), ("fixture_digest", fixture_digest), ("migration_digest", migration_digest)):
        if not DIGEST_RE.fullmatch(_text(value)):
            raise Pkt24RehearsalError(f"{name}_must_be_sha256_digest")
    receipt: dict[str, Any] = {
        "schema_version": "0.1",
        "packet": PACKET,
        "status": PREPARATORY_ONLY,
        "base": {"ref": PROTECTED_BASE_REF, "commit": derived_base, "tree": base_tree},
        "candidate": {"origin": normalized_origin, "ref": ref, "commit": commit, "tree": tree, "clean_checkout": True},
        "package": {"config_digest": config_digest, "fixture_digest": fixture_digest, "migration_digest": migration_digest, "changed_paths": derived_paths, "outside_owned_paths": outside},
        "dependencies": {"holds": list(DEPENDENCY_HOLDS), "status": "UNRESOLVED"},
        "claims": {"qualification_claimed": False, "selectable": False, "provider_live": False, "consumer_proven": False, "vps_proven": False, "deployment_performed": False, "activation_claimed": False},
        "admission": {"admissible": False, "reason_codes": ["dependency_pkt22_unresolved", "dependency_pkt23_unresolved", "preparatory_only_receipt", "external_proof_absent"]},
    }
    receipt["receipt_digest"] = _canonical_digest(receipt)
    return receipt


def validate_receipt(receipt: Mapping[str, Any]) -> list[str]:
    """Return receipt violations; never upgrades a receipt to an approval."""

    errors: list[str] = []
    if _text(receipt.get("status")) != PREPARATORY_ONLY:
        errors.append("status_must_be_PREPARATORY_ONLY")
    if (receipt.get("admission") or {}).get("admissible") is not False:
        errors.append("admission_must_be_false")
    claims = receipt.get("claims") or {}
    for field in ("qualification_claimed", "selectable", "provider_live", "consumer_proven", "vps_proven", "deployment_performed", "activation_claimed"):
        if claims.get(field) is not False:
            errors.append(f"claim_must_be_false:{field}")
    package = receipt.get("package") or {}
    if package.get("outside_owned_paths"):
        errors.append("outside_owned_paths_present")
    base = receipt.get("base") or {}
    if base.get("ref") != PROTECTED_BASE_REF or not COMMIT_RE.fullmatch(_text(base.get("commit"))) or not TREE_RE.fullmatch(_text(base.get("tree"))):
        errors.append("base_identity_malformed")
    candidate = receipt.get("candidate") or {}
    try:
        _explicit_ref(candidate.get("ref"))
    except Pkt24RehearsalError:
        errors.append("candidate_ref_malformed")
    if candidate.get("origin") != EXPECTED_ORIGIN or candidate.get("clean_checkout") is not True or not COMMIT_RE.fullmatch(_text(candidate.get("commit"))) or not TREE_RE.fullmatch(_text(candidate.get("tree"))):
        errors.append("candidate_identity_malformed")
    changed = package.get("changed_paths")
    if not isinstance(changed, list) or changed != sorted(set(changed)) or any(not _is_allowed_path(_text(path)) for path in changed):
        errors.append("changed_paths_malformed")
    for name in ("config_digest", "fixture_digest", "migration_digest"):
        if not DIGEST_RE.fullmatch(_text(package.get(name))):
            errors.append(f"{name}_malformed")
    supplied_digest = _text(receipt.get("receipt_digest"))
    unsigned = dict(receipt)
    unsigned.pop("receipt_digest", None)
    if supplied_digest != _canonical_digest(unsigned):
        errors.append("receipt_digest_mismatch")
    return errors


__all__ = [
    "DEPENDENCY_HOLDS",
    "MIGRATION_MANIFEST",
    "PACKET",
    "PREPARATORY_ONLY",
    "Pkt24RehearsalError",
    "bind_preparatory_receipt",
    "read_physical_checkout_ref",
    "sanitize_origin",
    "validate_local_fixture",
    "validate_migration_manifest",
    "validate_receipt",
]
