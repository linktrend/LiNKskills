"""Isolated deterministic workspace for eval fixture lifecycle."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable, Optional, Union


class EvalWorkspace:
    """Temporary workspace that seeds fixtures and retains a cleanup receipt."""

    def __init__(self, *, prefix: str = "linkskills-eval-", base_dir: Optional[Path] = None) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix=prefix, dir=base_dir)
        self.root = Path(self._tmpdir.name)
        self.fixtures_dir = self.root / "fixtures"
        self.outputs_dir = self.root / "outputs"
        self.evidence_dir = self.root / "evidence"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self._seeded: list[str] = []
        self._closed = False

    def seed_bytes(self, relative_name: str, content: bytes) -> Path:
        """Write fixture bytes under fixtures/ and record the path."""
        target = self.fixtures_dir / relative_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        self._seeded.append(str(target.relative_to(self.root)))
        return target

    def seed_text(self, relative_name: str, content: str, *, encoding: str = "utf-8") -> Path:
        """Write fixture text under fixtures/."""
        return self.seed_bytes(relative_name, content.encode(encoding))

    def copy_fixtures(
        self,
        source: Union[str, Path],
        *,
        dest_name: str = ".",
    ) -> Path:
        """Copy a fixture file or directory into the workspace fixtures tree."""
        src = Path(source)
        if not src.exists():
            raise FileNotFoundError(f"fixture source not found: {src}")
        dest = self.fixtures_dir / dest_name
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            for path in dest.rglob("*"):
                if path.is_file():
                    self._seeded.append(str(path.relative_to(self.root)))
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            self._seeded.append(str(dest.relative_to(self.root)))
        return dest

    def copy_fixture_paths(self, paths: Iterable[Union[str, Path]]) -> list[Path]:
        """Copy multiple fixture paths into fixtures/, preserving basenames."""
        copied: list[Path] = []
        for path in paths:
            src = Path(path)
            copied.append(self.copy_fixtures(src, dest_name=src.name))
        return copied

    def write_output(self, case_id: str, content: str, *, encoding: str = "utf-8") -> Path:
        """Persist observed output for a case and return its path."""
        safe = case_id.replace("/", "_")
        path = self.outputs_dir / f"{safe}.txt"
        path.write_text(content, encoding=encoding)
        return path

    def copy_tree(self, source: Path, dest_name: str = "bundle") -> Path:
        """Copy a source directory into the workspace."""
        dest = self.root / dest_name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        return dest

    def file_hash(self, path: Path) -> str:
        """SHA-256 hex digest of a file."""
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def receipt(self) -> dict[str, Any]:
        """Return workspace evidence suitable for run persistence."""
        return {
            "root": str(self.root),
            "seeded_fixtures": list(self._seeded),
            "closed": self._closed,
        }

    def cleanup(self) -> dict[str, Any]:
        """Tear down the temporary directory and return a cleanup receipt."""
        receipt = self.receipt()
        if not self._closed:
            self._tmpdir.cleanup()
            self._closed = True
            receipt["closed"] = True
        return receipt

    def __enter__(self) -> "EvalWorkspace":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()


def create_workspace(
    *,
    fixtures: Optional[Iterable[Union[str, Path]]] = None,
    fixture_dir: Optional[Union[str, Path]] = None,
    prefix: str = "linkskills-eval-",
) -> EvalWorkspace:
    """Create an isolated temp workspace and optionally copy fixtures into it."""
    workspace = EvalWorkspace(prefix=prefix)
    if fixture_dir is not None:
        workspace.copy_fixtures(fixture_dir, dest_name="suite")
    if fixtures:
        workspace.copy_fixture_paths(fixtures)
    return workspace
