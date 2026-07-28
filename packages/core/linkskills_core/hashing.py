"""Shared canonical hashing for LiNKskills release / eval / profile identity.

Authoritative algorithms used by publisher, validator, Eval Runner, and
certification. Prefer these helpers over ad-hoc SHA digests.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

UNSET_SKILL_RELEASE_HASH = "skill-release:unset"
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_SKIP_NAMES = {".DS_Store", "Thumbs.db"}
# Stamped profile embeds skill_bundle_hash; exclude it from that bundle's content hash.
BUNDLE_CONTENT_EXCLUDES = frozenset({"references/execution-profile.json"})


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_hex_text(text: str) -> str:
    return sha256_hex_bytes(text.encode("utf-8"))


def sha256_hex_file(path: Union[str, Path]) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_prefixed(digest_hex: str) -> str:
    text = str(digest_hex).strip()
    if text.startswith("sha256:"):
        return text
    return f"sha256:{text}"


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def request_hash(payload: Mapping[str, Any]) -> str:
    """Stable bare SHA-256 hex for gateway idempotency request binding."""
    return sha256_hex_text(canonical_json(payload))


def iter_skill_files(
    skill_dir: Path,
    *,
    exclude_relpaths: Optional[Sequence[str]] = None,
) -> list[Path]:
    root = Path(skill_dir).resolve()
    excluded = set(exclude_relpaths or ())
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in _SKIP_NAMES or path.name.startswith("."):
            continue
        rel = path.resolve().relative_to(root).as_posix()
        if rel in excluded:
            continue
        files.append(path)
    return files


def directory_manifest_digest(
    root: Union[str, Path],
    files: Optional[Sequence[Path]] = None,
    *,
    exclude_relpaths: Optional[Sequence[str]] = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Bare 64-hex digest over sorted ``relpath\\0file_sha\\n`` lines."""
    base = Path(root).resolve()
    entries = (
        list(files)
        if files is not None
        else iter_skill_files(base, exclude_relpaths=exclude_relpaths)
    )
    entry_hashes: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for path in sorted(entries, key=lambda p: p.resolve().relative_to(base).as_posix()):
        rel = path.resolve().relative_to(base).as_posix()
        file_hash = sha256_hex_file(path)
        size = path.stat().st_size
        entry_hashes.append({"path": rel, "sha256": file_hash, "size": size})
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), entry_hashes


def content_hash_for_directory(
    root: Union[str, Path],
    files: Optional[Sequence[Path]] = None,
    *,
    exclude_relpaths: Optional[Sequence[str]] = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Canonical content hash ``sha256:<hex>`` for a skill/release directory."""
    digest, entries = directory_manifest_digest(
        root, files=files, exclude_relpaths=exclude_relpaths
    )
    return sha256_prefixed(digest), entries


def skill_release_hash(skill_dir: Optional[Union[str, Path]]) -> str:
    """Tree hash for an immutable skill-release directory.

    Uses the same directory digest as ``content_hash_for_directory`` with a
    ``skill-release:`` prefix so publisher and Eval Runner agree on the body.
    Includes stamped execution-profile.json (full release identity).
    """
    if skill_dir is None:
        return UNSET_SKILL_RELEASE_HASH
    root = Path(skill_dir)
    if not root.is_dir():
        return UNSET_SKILL_RELEASE_HASH
    digest, _ = directory_manifest_digest(root)
    return f"skill-release:{digest}"


def eval_suite_file_hash(skill_dir: Union[str, Path]) -> Optional[str]:
    """Hash the canonical eval suite file (JSON preferred, then YAML)."""
    root = Path(skill_dir)
    for candidate in (
        root / "references" / "eval-suite.json",
        root / "eval-suite.json",
        root / "references" / "eval-suite.yaml",
        root / "references" / "eval-suite.yml",
        root / "eval-suite.yaml",
        root / "eval-suite.yml",
    ):
        if candidate.is_file():
            return sha256_prefixed(sha256_hex_file(candidate))
    return None


def eval_suite_document_hash(raw_text: str) -> str:
    """Bare hex hash of suite document bytes (Eval Runner suite_hash field)."""
    return sha256_hex_text(raw_text)


def parse_simple_frontmatter(text: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"name", "version", "description", "format_profile"}:
            meta[key] = value
    return meta


def discover_fragments(
    skill_dir: Path,
    entry_hashes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fragments: list[dict[str, Any]] = []
    by_path = {e["path"]: e["sha256"] for e in entry_hashes}
    if "SKILL.md" in by_path:
        fragments.append(
            {
                "fragment_id": "skill-md",
                "disclosure_level": 2,
                "path": "SKILL.md",
                "content_hash": sha256_prefixed(by_path["SKILL.md"]),
            }
        )
    for path in sorted(by_path):
        if path.startswith("references/") and path.endswith((".md", ".yaml", ".yml", ".json")):
            if path.endswith(("eval-suite.yaml", "eval-suite.yml", "eval-suite.json")):
                continue
            if path in BUNDLE_CONTENT_EXCLUDES:
                continue
            level = 5 if "example" in path or "schema" in path else 3
            fragments.append(
                {
                    "fragment_id": path.replace("/", "__"),
                    "disclosure_level": level,
                    "path": path,
                    "content_hash": sha256_prefixed(by_path[path]),
                }
            )
    return fragments


def skill_bundle_identity_hash(
    *,
    skill_id: str,
    version: str,
    content_hash: str,
    eval_suite_hash: Optional[str],
    fragments: Sequence[Mapping[str, Any]],
) -> str:
    identity = {
        "skill_id": skill_id,
        "version": version,
        "content_hash": content_hash,
        "eval_suite_hash": eval_suite_hash,
        "fragments": [
            {"path": f["path"], "content_hash": f["content_hash"]} for f in fragments
        ],
    }
    return sha256_prefixed(sha256_hex_text(canonical_json(identity)))


def build_skill_bundle_manifest(skill_dir: Union[str, Path]) -> dict[str, Any]:
    """Authoritative Skill Pack bundle manifest (publisher + profile stamping).

    Content hash excludes stamped ``references/execution-profile.json`` so the
    profile can embed ``skill_bundle_hash`` without a circular dependency.
    Full-tree ``skill_release_hash`` still includes the stamped profile.
    """
    root = Path(skill_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"skill directory not found: {root}")

    meta: dict[str, Any] = {}
    skill_md = root / "SKILL.md"
    if skill_md.is_file():
        meta = parse_simple_frontmatter(skill_md.read_text(encoding="utf-8"))

    skill_id = str(meta.get("name") or root.name)
    version = str(meta.get("version") or "0.0.0")
    content_hash, entry_hashes = content_hash_for_directory(
        root, exclude_relpaths=sorted(BUNDLE_CONTENT_EXCLUDES)
    )
    fragments = discover_fragments(root, entry_hashes)
    eval_hash = eval_suite_file_hash(root)
    bundle_hash = skill_bundle_identity_hash(
        skill_id=skill_id,
        version=version,
        content_hash=content_hash,
        eval_suite_hash=eval_hash,
        fragments=fragments,
    )
    return {
        "schema_version": "0.1",
        "skill_id": skill_id,
        "version": version,
        "content_hash": content_hash,
        "fragments": fragments,
        "eval_suite_hash": eval_hash,
        "file_count": len(entry_hashes),
        "entry_hashes": entry_hashes,
        "bundle_hash": bundle_hash,
    }


def execution_profile_identity_hash(profile: Mapping[str, Any]) -> str:
    """Hash stable execution-profile identity fields (excludes certification blob)."""
    identity = {
        "adapter": dict(profile.get("adapter") or {}),
        "eval_suite_hash": profile.get("eval_suite_hash"),
        "eval_suite_id": profile.get("eval_suite_id"),
        "execution_profile_id": profile.get("execution_profile_id"),
        "lifecycle_state": profile.get("lifecycle_state"),
        "model_capability_tier": profile.get("model_capability_tier"),
        "runtime_profile_id": profile.get("runtime_profile_id"),
        "skill_bundle_hash": profile.get("skill_bundle_hash"),
        "skill_id": profile.get("skill_id"),
        "skill_version": profile.get("skill_version"),
        "toolchain": list(profile.get("toolchain") or []),
    }
    return sha256_prefixed(sha256_hex_text(canonical_json(identity)))


def stamp_execution_profile(
    skill_dir: Union[str, Path],
    *,
    runtime_profile_id: str = "cursor-macos",
    adapter_name: str = "local-actor",
    adapter_version_range: str = ">=0.1.0",
    model_capability_tier: str = "balanced",
    lifecycle_state: str = "draft",
) -> dict[str, Any]:
    """Build an authoritative draft execution-profile from the skill directory."""
    root = Path(skill_dir).resolve()
    bundle = build_skill_bundle_manifest(root)
    skill_id = str(bundle["skill_id"])
    version = str(bundle["version"])
    eval_hash = bundle.get("eval_suite_hash")
    if not eval_hash:
        raise ValueError(f"skill {skill_id} missing canonical eval suite for profile stamp")
    suite_doc = root / "references" / "eval-suite.json"
    suite_id = f"{skill_id}-eval"
    if suite_doc.is_file():
        try:
            payload = json.loads(suite_doc.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and payload.get("suite_id"):
                suite_id = str(payload["suite_id"])
        except json.JSONDecodeError:
            pass
    profile: dict[str, Any] = {
        "schema_version": "0.1",
        "execution_profile_id": f"{skill_id}-{runtime_profile_id}-draft",
        "skill_id": skill_id,
        "skill_version": version,
        "skill_bundle_hash": str(bundle["bundle_hash"]),
        "eval_suite_id": suite_id,
        "eval_suite_hash": str(eval_hash),
        "toolchain": [],
        "adapter": {"name": adapter_name, "version_range": adapter_version_range},
        "runtime_profile_id": runtime_profile_id,
        "model_capability_tier": model_capability_tier,
        "lifecycle_state": lifecycle_state,
        "certification": {
            "status": "uncertified",
            "refusal_reason": (
                "Canonical artifacts stamped via shared hashing; live certification not claimed"
            ),
        },
    }
    profile["profile_hash"] = execution_profile_identity_hash(profile)
    return profile


def verify_execution_profile_hashes(
    skill_dir: Union[str, Path],
    profile: Optional[Mapping[str, Any]] = None,
) -> list[str]:
    """Recalculate and compare cross-artifact hashes for an execution profile."""
    root = Path(skill_dir).resolve()
    errors: list[str] = []
    if profile is None:
        path = root / "references" / "execution-profile.json"
        if not path.is_file():
            return [f"{root.name}: missing references/execution-profile.json"]
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return [f"{root.name}: invalid execution-profile JSON ({exc})"]
        if not isinstance(loaded, dict):
            return [f"{root.name}: execution-profile must be an object"]
        profile = loaded
    bundle = build_skill_bundle_manifest(root)
    expected_eval = bundle.get("eval_suite_hash")
    expected_bundle = str(bundle["bundle_hash"])
    if str(profile.get("eval_suite_hash") or "") != str(expected_eval or ""):
        errors.append(
            f"{root.name}: eval_suite_hash mismatch "
            f"(profile={profile.get('eval_suite_hash')!r} recalculated={expected_eval!r})"
        )
    if str(profile.get("skill_bundle_hash") or "") != expected_bundle:
        errors.append(
            f"{root.name}: skill_bundle_hash mismatch "
            f"(profile={profile.get('skill_bundle_hash')!r} recalculated={expected_bundle!r})"
        )
    expected_profile = execution_profile_identity_hash(profile)
    if str(profile.get("profile_hash") or "") != expected_profile:
        errors.append(
            f"{root.name}: profile_hash mismatch "
            f"(profile={profile.get('profile_hash')!r} recalculated={expected_profile!r})"
        )
    return errors
