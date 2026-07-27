"""Exact tool version/hash resolution tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linkskills_tool_runtime.descriptor import load_tool_descriptor
from linkskills_tool_runtime.resolve import ResolutionError, resolve_tool


def test_resolve_exact_version_and_hash(tmp_path: Path):
    tool_dir = tmp_path / "echo-tool"
    tool_dir.mkdir()
    (tool_dir / "descriptor.yaml").write_text(
        """
schema_version: "0.1"
tool_id: echo-tool
version: 1.2.3
description: Echo canary tool
side_effect_class: read_only
lifecycle_state: usable
bundle_hash: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
source_hash: "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
entrypoint:
  transport: cli
  command: echo
platforms:
  - any
""".strip()
        + "\n",
        encoding="utf-8",
    )

    resolved = resolve_tool(
        tool_dir,
        tool_id="echo-tool",
        version="1.2.3",
        bundle_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        source_hash="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    )
    assert resolved.version == "1.2.3"
    assert resolved.bundle_hash.endswith("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")


def test_resolve_rejects_version_and_hash_mismatch(tmp_path: Path):
    tool_dir = tmp_path / "echo-tool"
    tool_dir.mkdir()
    (tool_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "echo-tool",
                "version": "1.0.0",
                "description": "from package.json",
                "side_effect_class": "read_only",
                "bundle_hash": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ResolutionError, match="version mismatch"):
        resolve_tool(tool_dir, version="9.9.9")

    with pytest.raises(ResolutionError, match="bundle_hash mismatch"):
        resolve_tool(
            tool_dir,
            version="1.0.0",
            bundle_hash="sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        )

    with pytest.raises(ResolutionError, match="latest"):
        resolve_tool(tool_dir, version="latest")


def test_synthesize_descriptor_when_missing(tmp_path: Path):
    tool_dir = tmp_path / "mystery-tool"
    tool_dir.mkdir()
    descriptor = load_tool_descriptor(tool_dir)
    assert descriptor.tool_id == "mystery-tool"
    assert descriptor.side_effect_class == "unknown"
    assert descriptor.synthesized is True
    assert descriptor.lifecycle_state == "draft"
