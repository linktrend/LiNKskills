"""Exact version/hash resolution for packaged tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .descriptor import ToolDescriptor, load_tool_descriptor


class ResolutionError(ValueError):
    """Raised when a tool cannot be resolved to the requested version/hash."""


@dataclass(frozen=True)
class ResolvedTool:
    """Exact tool binding for invocation."""

    descriptor: ToolDescriptor
    tool_dir: Path
    requested_version: Optional[str] = None
    requested_bundle_hash: Optional[str] = None
    requested_source_hash: Optional[str] = None

    @property
    def tool_id(self) -> str:
        return self.descriptor.tool_id

    @property
    def version(self) -> str:
        return self.descriptor.version

    @property
    def bundle_hash(self) -> Optional[str]:
        return self.descriptor.bundle_hash


def resolve_tool(
    tool_dir: Union[str, Path],
    *,
    tool_id: Optional[str] = None,
    version: Optional[str] = None,
    bundle_hash: Optional[str] = None,
    source_hash: Optional[str] = None,
) -> ResolvedTool:
    """Resolve a tool directory to an exact descriptor binding.

    Rejects version/hash mismatches. Floating "latest" is not accepted when a
    concrete version is required by the caller.
    """
    path = Path(tool_dir).resolve()
    descriptor = load_tool_descriptor(path)

    if tool_id is not None and descriptor.tool_id != tool_id:
        raise ResolutionError(
            f"tool_id mismatch: expected {tool_id!r}, found {descriptor.tool_id!r}"
        )

    if version is not None:
        if version == "latest":
            raise ResolutionError('refusing floating version "latest"; pin an exact version')
        if descriptor.version != version:
            raise ResolutionError(
                f"version mismatch for {descriptor.tool_id}: "
                f"expected {version!r}, found {descriptor.version!r}"
            )

    if bundle_hash is not None:
        if not descriptor.bundle_hash:
            raise ResolutionError(
                f"bundle_hash required ({bundle_hash!r}) but descriptor has none "
                f"for {descriptor.tool_id}"
            )
        if descriptor.bundle_hash != bundle_hash:
            raise ResolutionError(
                f"bundle_hash mismatch for {descriptor.tool_id}: "
                f"expected {bundle_hash!r}, found {descriptor.bundle_hash!r}"
            )

    if source_hash is not None:
        if not descriptor.source_hash:
            raise ResolutionError(
                f"source_hash required ({source_hash!r}) but descriptor has none "
                f"for {descriptor.tool_id}"
            )
        if descriptor.source_hash != source_hash:
            raise ResolutionError(
                f"source_hash mismatch for {descriptor.tool_id}: "
                f"expected {source_hash!r}, found {descriptor.source_hash!r}"
            )

    return ResolvedTool(
        descriptor=descriptor,
        tool_dir=path,
        requested_version=version,
        requested_bundle_hash=bundle_hash,
        requested_source_hash=source_hash,
    )
