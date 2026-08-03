"""Catalog provenance: governed source commit + source_tree_sha256.

``catalog/index.json`` must never claim a self-referential tip SHA (the commit
that embeds the catalog cannot equal ``git_sha``). Instead:

* ``git_sha`` — exact ancestor commit whose **governed certification inputs**
  were certified (skills/tools/runtime packages/scripts used by sealing).
* ``source_tree_sha256`` — deterministic SHA-256 over those tracked inputs.

Generated ``catalog/``, ``evidence/``, ``docs/``, migrations, tests, and
runtime noise are excluded so documentation-only follow-up commits do not
invalidate a still-matching source tree.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

ZERO_GIT_SHA = "0" * 40
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_TREE_SHA_RE = re.compile(r"^[0-9a-f]{64}$")

# Tracked path prefixes that participate in sealed certification outcomes.
GOVERNED_INPUT_PREFIXES: Tuple[str, ...] = (
    "skills/",
    "tools/",
    "packages/contracts/",
    "packages/core/",
    "packages/eval_runner/",
    "packages/tool_runtime/",
    "packages/publisher/",
    "lib/skill_runtime/",
    "scripts/certify-catalog.py",
    "scripts/build-catalog-index.py",
    "scripts/run-sealed-linux-certify.sh",
    "validator.py",
)

# Explicit exclusions inside otherwise-governed trees (generated/runtime/vendor noise).
_EXCLUDED_PATH_PARTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "tmp",
        "node_modules",
        "dist",
        "build",
        ".egg-info",
    }
)
_EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo", ".so", ".dylib", ".sb"})


def is_governed_input_path(relpath: str) -> bool:
    """Return True when a repo-relative path is a governed certification input."""
    norm = relpath.replace("\\", "/").lstrip("./")
    if not norm or norm.endswith("/"):
        return False
    if not any(
        norm == prefix.rstrip("/") or norm.startswith(prefix)
        for prefix in GOVERNED_INPUT_PREFIXES
    ):
        return False
    parts = norm.split("/")
    if any(part in _EXCLUDED_PATH_PARTS for part in parts[:-1]):
        return False
    if any(part.endswith(".egg-info") for part in parts):
        return False
    name = parts[-1]
    if name.startswith("."):
        return False
    suffix = Path(name).suffix.lower()
    if suffix in _EXCLUDED_SUFFIXES:
        return False
    # Vendored trees are not certification-governed package sources.
    if norm.startswith("tools/gws/vendor/"):
        return False
    return True


def _git(
    repo_root: Path,
    args: Sequence[str],
    *,
    check: bool = True,
    input_bytes: Optional[bytes] = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _list_governed_input_paths_fs(repo_root: Path) -> List[str]:
    """Filesystem fallback for clean archives / containers without git metadata."""
    root = Path(repo_root).resolve()
    found: List[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if is_governed_input_path(rel):
            found.append(rel)
    return sorted(set(found))


def list_governed_input_paths(
    repo_root: Path,
    *,
    commit: Optional[str] = None,
) -> List[str]:
    """List sorted repo-relative governed input paths (tracked git, else FS)."""
    root = Path(repo_root).resolve()
    if commit:
        proc = _git(root, ["ls-tree", "-r", "--name-only", commit], check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"git list failed for governed inputs at {commit}: "
                f"{proc.stderr.decode('utf-8', 'replace')}"
            )
        paths = proc.stdout.decode("utf-8").splitlines()
        return sorted({p for p in paths if is_governed_input_path(p)})

    proc = _git(
        root,
        ["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=False,
    )
    if proc.returncode == 0:
        # Confirm this directory is the git toplevel (avoid parent-repo bleed).
        top = _git(root, ["rev-parse", "--show-toplevel"], check=False)
        if top.returncode == 0:
            toplevel = Path(top.stdout.decode("utf-8").strip()).resolve()
            if toplevel == root:
                paths = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
                return sorted({p for p in paths if is_governed_input_path(p)})
    return _list_governed_input_paths_fs(root)


def _file_digest_at(
    repo_root: Path,
    relpath: str,
    *,
    commit: Optional[str],
) -> bytes:
    root = Path(repo_root).resolve()
    if commit:
        proc = _git(root, ["show", f"{commit}:{relpath}"], check=False)
        if proc.returncode != 0:
            raise FileNotFoundError(f"missing {relpath} at {commit}")
        return hashlib.sha256(proc.stdout).digest()
    path = root / relpath
    if not path.is_file():
        raise FileNotFoundError(f"missing governed input file: {relpath}")
    return hashlib.sha256(path.read_bytes()).digest()


def compute_source_tree_sha256(
    repo_root: Path,
    *,
    commit: Optional[str] = None,
    paths: Optional[Iterable[str]] = None,
) -> str:
    """Deterministic SHA-256 over governed input paths (path + file digest).

    Layout: for each sorted path, update with ``path\\0`` + hex file sha + ``\\0``.
    """
    root = Path(repo_root).resolve()
    ordered = (
        sorted({p for p in paths if is_governed_input_path(p)})
        if paths is not None
        else list_governed_input_paths(root, commit=commit)
    )
    digest = hashlib.sha256()
    for relpath in ordered:
        digest.update(relpath.encode("utf-8"))
        digest.update(b"\0")
        file_hex = _file_digest_at(root, relpath, commit=commit).hex().encode("ascii")
        digest.update(file_hex)
        digest.update(b"\0")
    return digest.hexdigest()


def normalize_git_sha(value: Optional[str]) -> Optional[str]:
    """Return lowercase 40-hex SHA or None when empty."""
    if value is None:
        return None
    text = value.strip().lower()
    return text or None


def is_all_zero_git_sha(value: Optional[str]) -> bool:
    """Return True for missing/empty/all-zero commit placeholders."""
    sha = normalize_git_sha(value)
    return sha is None or sha == ZERO_GIT_SHA or set(sha) == {"0"}


def git_object_exists(repo_root: Path, git_sha: str) -> bool:
    """Return True when ``git_sha`` resolves to a git object in ``repo_root``."""
    proc = _git(
        Path(repo_root).resolve(),
        ["cat-file", "-e", f"{git_sha}^{{commit}}"],
        check=False,
    )
    return proc.returncode == 0


def is_ancestor_commit(repo_root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    """Return True when ``ancestor`` is an ancestor of ``descendant`` (inclusive)."""
    proc = _git(
        Path(repo_root).resolve(),
        ["merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
    )
    return proc.returncode == 0


def resolve_source_commit(
    repo_root: Path,
    *,
    explicit: Optional[str] = None,
    head: str = "HEAD",
    allow_unverified_pin: bool = False,
) -> str:
    """Resolve the governed source commit for catalog provenance.

    Preference order:
    1. Explicit pin (``LINKSKILLS_CATALOG_GIT_SHA`` / caller).
    2. ``HEAD`` when the working tree's governed hash matches ``HEAD``.

    Never invents a self-referential tip for a commit that will embed the catalog.
    ``allow_unverified_pin`` is for sealed containers that receive a host-validated
    pin but lack a git object database.
    """
    root = Path(repo_root).resolve()
    pinned = normalize_git_sha(explicit)
    if pinned:
        if is_all_zero_git_sha(pinned) or not GIT_SHA_RE.fullmatch(pinned):
            raise ValueError(f"invalid catalog source git_sha: {pinned!r}")
        if git_object_exists(root, pinned):
            return pinned
        if allow_unverified_pin:
            return pinned
        raise ValueError(f"catalog source git_sha is not a commit: {pinned}")

    head_proc = _git(root, ["rev-parse", head], check=False)
    if head_proc.returncode != 0:
        raise ValueError(f"unable to resolve {head} for catalog provenance")
    head_sha = head_proc.stdout.decode("utf-8").strip().lower()
    working = compute_source_tree_sha256(root)
    at_head = compute_source_tree_sha256(root, commit=head_sha)
    if working != at_head:
        raise ValueError(
            "governed inputs differ from HEAD; set LINKSKILLS_CATALOG_GIT_SHA to the "
            "exact ancestor commit being certified"
        )
    return head_sha


def validate_catalog_provenance(
    index: Dict[str, Any],
    repo_root: Path,
    *,
    head: str = "HEAD",
) -> List[str]:
    """Return human-readable errors when catalog provenance is invalid."""
    root = Path(repo_root).resolve()
    errors: List[str] = []

    git_sha = normalize_git_sha(index.get("git_sha") if isinstance(index.get("git_sha"), str) else None)
    source_tree = index.get("source_tree_sha256")
    source_tree_s = (
        source_tree.strip().lower() if isinstance(source_tree, str) else None
    )

    if is_all_zero_git_sha(git_sha):
        errors.append("catalog git_sha is missing or all-zero")
    elif git_sha is None or not GIT_SHA_RE.fullmatch(git_sha):
        errors.append(f"catalog git_sha is not a 40-hex commit: {git_sha!r}")
    elif not git_object_exists(root, git_sha):
        errors.append(f"catalog git_sha is not a commit in this repository: {git_sha}")
    elif not is_ancestor_commit(root, git_sha, head):
        errors.append(
            f"catalog git_sha {git_sha} is not an ancestor of {head} "
            "(unrelated or divergent commit)"
        )

    if not source_tree_s or not SOURCE_TREE_SHA_RE.fullmatch(source_tree_s):
        errors.append(
            f"catalog source_tree_sha256 missing or malformed: {source_tree!r}"
        )
        return errors

    try:
        current = compute_source_tree_sha256(root)
    except (RuntimeError, FileNotFoundError) as exc:
        errors.append(f"unable to hash current governed inputs: {exc}")
        return errors

    if current != source_tree_s:
        errors.append(
            "catalog source_tree_sha256 does not match current governed inputs "
            f"(index={source_tree_s} current={current})"
        )

    if git_sha and GIT_SHA_RE.fullmatch(git_sha) and git_object_exists(root, git_sha):
        try:
            at_commit = compute_source_tree_sha256(root, commit=git_sha)
        except (RuntimeError, FileNotFoundError) as exc:
            errors.append(
                f"unable to hash governed inputs at git_sha {git_sha}: {exc}"
            )
            return errors
        if at_commit != source_tree_s:
            errors.append(
                "catalog git_sha governed inputs do not match source_tree_sha256 "
                f"(git_sha={git_sha} at_commit={at_commit} index={source_tree_s})"
            )
        if at_commit != current:
            errors.append(
                "governed inputs at catalog git_sha drifted from the working tree "
                f"(at_commit={at_commit} current={current})"
            )

    return errors


def build_provenance_fields(
    repo_root: Path,
    *,
    git_sha: Optional[str] = None,
    source_tree_sha256: Optional[str] = None,
) -> Dict[str, str]:
    """Compute ``git_sha`` + ``source_tree_sha256`` for catalog index emission.

    Hosts with git validate the source commit object. Sealed containers may pass
    both pins (``LINKSKILLS_CATALOG_GIT_SHA`` + ``LINKSKILLS_SOURCE_TREE_SHA256``)
    after the host verified them; the working-tree governed hash must still match.
    """
    root = Path(repo_root).resolve()
    pinned_tree = (
        source_tree_sha256.strip().lower() if isinstance(source_tree_sha256, str) else None
    )
    if pinned_tree and not SOURCE_TREE_SHA_RE.fullmatch(pinned_tree):
        raise ValueError(f"invalid source_tree_sha256 pin: {source_tree_sha256!r}")

    working = compute_source_tree_sha256(root)
    allow_unverified = bool(git_sha) and (
        pinned_tree is not None or not git_object_exists(root, normalize_git_sha(git_sha) or "")
    )
    source_commit = resolve_source_commit(
        root,
        explicit=git_sha,
        allow_unverified_pin=allow_unverified,
    )

    if git_object_exists(root, source_commit):
        tree_hash = compute_source_tree_sha256(root, commit=source_commit)
    else:
        # Clean archive / container: trust working-tree hash (+ optional host pin).
        tree_hash = working

    if pinned_tree and pinned_tree != tree_hash:
        raise ValueError(
            "source_tree_sha256 pin does not match governed inputs: "
            f"pin={pinned_tree} computed={tree_hash}"
        )
    if working != tree_hash:
        raise ValueError(
            "working-tree governed inputs differ from source commit "
            f"{source_commit}: working={working} source={tree_hash}"
        )
    return {
        "git_sha": source_commit,
        "source_tree_sha256": tree_hash,
    }
