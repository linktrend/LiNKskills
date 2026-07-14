from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .frontmatter import extract_frontmatter
from .types import (
    CapabilityContract,
    CapabilitySourceType,
    CatalogSnapshot,
    ExecutionMode,
    LifecycleState,
    PackageContract,
    SourceTrace,
    VisibilityClass,
)

EXTRACTOR_VERSION = "phase0-3-v1"


class RegistryError(RuntimeError):
    """Registry extraction failure."""


@dataclass
class ExtractionResult:
    snapshot: CatalogSnapshot
    warnings: List[str]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RegistryError(f"Failed to parse JSON file {path}: {exc}") from exc


def _resolve_repo_path(repo_root: Path, manifest_path: str) -> Path:
    normalized = manifest_path[1:] if manifest_path.startswith("/") else manifest_path
    return (repo_root / normalized).resolve()


def _locate_skill_dir(target_path: Path) -> Path:
    candidates: List[Path] = []
    if target_path.is_dir():
        candidates.append(target_path)
    else:
        candidates.append(target_path.parent)
    candidates.append(candidates[0].parent)

    for candidate in candidates:
        if (candidate / "SKILL.md").exists():
            return candidate
    raise RegistryError(f"Unable to locate skill directory from path: {target_path}")


def _locate_tool_dir(target_path: Path) -> Path:
    candidates: List[Path] = []
    if target_path.is_dir():
        candidates.extend([target_path, target_path.parent, target_path.parent.parent])
    else:
        parent = target_path.parent
        candidates.extend([parent, parent.parent, parent.parent.parent])

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "interface.json").exists():
            return candidate
    raise RegistryError(f"Unable to locate tool directory from path: {target_path}")


def _sha256_of_files(paths: List[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_commit_sha(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:
        return "unknown"


def _skill_schema_refs(skill_dir: Path) -> Tuple[str, str, List[str]]:
    schema_path = skill_dir / "references" / "schemas.json"
    payload = _read_json(schema_path)
    warnings: List[str] = []
    defs = payload.get("definitions")
    if isinstance(defs, dict) and defs:
        input_key = "input" if "input" in defs else next(iter(defs.keys()))
        output_key = "output" if "output" in defs else input_key
        if "input" not in defs or "output" not in defs:
            warnings.append(
                f"Schema {schema_path} missing standard input/output keys; "
                f"fallback applied ({input_key}/{output_key})"
            )
        return (
            f"{schema_path.as_posix()}#/definitions/{input_key}",
            f"{schema_path.as_posix()}#/definitions/{output_key}",
            warnings,
        )

    warnings.append(f"Schema {schema_path} missing definitions object; fallback applied to root")
    return (
        f"{schema_path.as_posix()}#/",
        f"{schema_path.as_posix()}#/",
        warnings,
    )


def _extract_skill_contract(
    repo_root: Path,
    entry: Dict[str, Any],
    commit_sha: str,
    extracted_at: str,
    warnings: List[str],
) -> CapabilityContract:
    uid = str(entry.get("uid", "")).strip()
    if not uid:
        raise RegistryError("Manifest entry is missing uid")

    target_path = _resolve_repo_path(repo_root, str(entry.get("path", "")))
    skill_dir = _locate_skill_dir(target_path)
    skill_md = skill_dir / "SKILL.md"
    schema_path = skill_dir / "references" / "schemas.json"
    changelog_path = skill_dir / "references" / "changelog.md"

    for required in (skill_md, schema_path, changelog_path):
        if not required.exists():
            raise RegistryError(f"Skill {uid} missing required artifact: {required}")

    frontmatter, errors = extract_frontmatter(skill_md.read_text(encoding="utf-8"))
    if errors or frontmatter is None:
        raise RegistryError(f"Skill {uid} frontmatter parse error: {errors}")

    input_ref, output_ref, schema_warnings = _skill_schema_refs(skill_dir)
    warnings.extend(schema_warnings)
    file_hash = _sha256_of_files([skill_md, schema_path, changelog_path])

    source_trace = SourceTrace(
        repo_commit_sha=commit_sha,
        source_path_hash=file_hash,
        extracted_at=extracted_at,
        extractor_version=EXTRACTOR_VERSION,
        source_paths=[
            str(skill_md.relative_to(repo_root)),
            str(schema_path.relative_to(repo_root)),
            str(changelog_path.relative_to(repo_root)),
        ],
    )

    return CapabilityContract(
        capability_id=uid,
        source_type=CapabilitySourceType.SKILL,
        version=str(entry.get("version", frontmatter.get("version", "0.0.0"))),
        name=str(frontmatter.get("name", uid)),
        description=str(frontmatter.get("description", entry.get("description", ""))),
        lifecycle_state=LifecycleState.INTERNAL,
        visibility=VisibilityClass.INTERNAL,
        execution_modes=[ExecutionMode.MANAGED],
        disclosure_mode="managed_server_disclosure",
        input_schema_ref=input_ref,
        output_schema_ref=output_ref,
        source_trace=source_trace,
    )


def _extract_tool_contract(repo_root: Path, entry: Dict[str, Any], commit_sha: str, extracted_at: str) -> CapabilityContract:
    uid = str(entry.get("uid", "")).strip()
    if not uid:
        raise RegistryError("Manifest tool entry is missing uid")

    target_path = _resolve_repo_path(repo_root, str(entry.get("path", "")))
    tool_dir = _locate_tool_dir(target_path)
    interface_path = tool_dir / "interface.json"
    readme_path = tool_dir / "README.md"

    for required in (interface_path, readme_path):
        if not required.exists():
            raise RegistryError(f"Tool {uid} missing required artifact: {required}")

    interface_payload = _read_json(interface_path)
    file_hash = _sha256_of_files([interface_path, readme_path])

    source_trace = SourceTrace(
        repo_commit_sha=commit_sha,
        source_path_hash=file_hash,
        extracted_at=extracted_at,
        extractor_version=EXTRACTOR_VERSION,
        source_paths=[
            str(interface_path.relative_to(repo_root)),
            str(readme_path.relative_to(repo_root)),
        ],
    )

    return CapabilityContract(
        capability_id=uid,
        source_type=CapabilitySourceType.TOOL,
        version=str(entry.get("version", "0.0.0")),
        name=str(interface_payload.get("name", uid)),
        description=str(interface_payload.get("description", entry.get("description", ""))),
        lifecycle_state=LifecycleState.INTERNAL,
        visibility=VisibilityClass.INTERNAL,
        execution_modes=[ExecutionMode.MANAGED],
        disclosure_mode="managed_server_disclosure",
        input_schema_ref=None,
        output_schema_ref=None,
        source_trace=source_trace,
    )


def _load_packages(packages_path: Path) -> List[PackageContract]:
    if not packages_path.exists():
        raise RegistryError(f"Package definition file not found: {packages_path}")
    payload = _read_json(packages_path)
    if not isinstance(payload, list):
        raise RegistryError("Package definition root must be a list")
    return [PackageContract(**item) for item in payload]


def build_registry_snapshot(repo_root: Path, manifest_path: Path, packages_path: Path) -> ExtractionResult:
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, list):
        raise RegistryError("manifest.json root must be a list")

    commit_sha = _git_commit_sha(repo_root)
    extracted_at = datetime.now(timezone.utc).isoformat()
    capabilities: List[CapabilityContract] = []
    warnings: List[str] = []

    for entry in manifest:
        if not isinstance(entry, dict):
            raise RegistryError("Manifest entries must be objects")
        entry_type = str(entry.get("type", "")).strip().lower()
        if entry_type == "skill":
            capabilities.append(_extract_skill_contract(repo_root, entry, commit_sha, extracted_at, warnings))
        elif entry_type == "tool":
            capabilities.append(_extract_tool_contract(repo_root, entry, commit_sha, extracted_at))
        else:
            raise RegistryError(f"Unsupported manifest type '{entry_type}' for uid={entry.get('uid')}")

    if len(capabilities) != len(manifest):
        raise RegistryError("Manifest coverage validation failed")

    for contract in capabilities:
        if not contract.lifecycle_state:
            raise RegistryError(f"Lifecycle default missing for capability {contract.capability_id}")

    packages = _load_packages(packages_path)

    snapshot = CatalogSnapshot(
        generated_at=extracted_at,
        repo_root=str(repo_root),
        manifest_entries=len(manifest),
        capabilities=capabilities,
        packages=packages,
        extraction_warnings=warnings,
    )
    return ExtractionResult(snapshot=snapshot, warnings=warnings)


def write_registry_snapshot(snapshot: CatalogSnapshot, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot.model_dump(mode="json"), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def load_registry_snapshot(path: Path) -> CatalogSnapshot:
    if not path.exists():
        raise RegistryError(f"Catalog file not found: {path}")
    payload = _read_json(path)
    return CatalogSnapshot(**payload)
