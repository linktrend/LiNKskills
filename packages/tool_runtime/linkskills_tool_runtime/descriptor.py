"""Load and normalize packaged tool descriptors from tools/<id>/."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union


@dataclass
class ToolDescriptor:
    """Normalized tool descriptor used by resolve/invoke."""

    tool_id: str
    version: str
    description: str
    entrypoint: dict[str, Any]
    platforms: list[str] = field(default_factory=lambda: ["any"])
    side_effect_class: str = "unknown"
    lifecycle_state: str = "draft"
    schema_version: str = "0.1"
    source_path: Optional[str] = None
    source_hash: Optional[str] = None
    bundle_hash: Optional[str] = None
    display_name: Optional[str] = None
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[float] = None
    raw: dict[str, Any] = field(default_factory=dict)
    synthesized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tool_id": self.tool_id,
            "version": self.version,
            "display_name": self.display_name,
            "description": self.description,
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "bundle_hash": self.bundle_hash,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "entrypoint": dict(self.entrypoint),
            "platforms": list(self.platforms),
            "side_effect_class": self.side_effect_class,
            "lifecycle_state": self.lifecycle_state,
            "timeout_seconds": self.timeout_seconds,
            "synthesized": self.synthesized,
        }


def _import_yaml():
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    return yaml


def _read_yaml_or_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        yaml = _import_yaml()
        if yaml is None:
            raise RuntimeError(f"PyYAML required to read {path}")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"descriptor must be a mapping: {path}")
    return data


def _parse_tool_md(path: Path) -> dict[str, Any]:
    """Extract a lightweight descriptor from TOOL.md frontmatter or headings."""
    text = path.read_text(encoding="utf-8")
    data: dict[str, Any] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            yaml = _import_yaml()
            if yaml is not None:
                parsed = yaml.safe_load(fm)
                if isinstance(parsed, dict):
                    data.update(parsed)
    # Fallback key: value lines under a Descriptor section.
    for match in re.finditer(
        r"^(tool_id|version|description|side_effect_class|lifecycle_state)\s*:\s*(.+)$",
        text,
        flags=re.MULTILINE,
    ):
        data.setdefault(match.group(1), match.group(2).strip().strip('"').strip("'"))
    return data


def _infer_entrypoint(tool_dir: Path, tool_id: str) -> dict[str, Any]:
    bin_dir = tool_dir / "bin"
    if bin_dir.is_dir():
        executables = sorted(p for p in bin_dir.iterdir() if p.is_file())
        if executables:
            return {
                "transport": "cli",
                "command": str(executables[0]),
                "working_directory": str(tool_dir),
            }
    return {
        "transport": "cli",
        "command": tool_id,
        "working_directory": str(tool_dir),
    }


def _normalize(raw: dict[str, Any], *, tool_dir: Path, synthesized: bool = False) -> ToolDescriptor:
    tool_id = str(raw.get("tool_id") or tool_dir.name)
    version = str(raw.get("version") or "0.0.0-draft")
    description = str(raw.get("description") or f"Draft descriptor for {tool_id}")
    entrypoint = raw.get("entrypoint")
    if not isinstance(entrypoint, dict):
        entrypoint = _infer_entrypoint(tool_dir, tool_id)
    platforms = raw.get("platforms") or ["any"]
    if isinstance(platforms, str):
        platforms = [platforms]
    side_effect = str(raw.get("side_effect_class") or "unknown")
    lifecycle = str(raw.get("lifecycle_state") or ("draft" if synthesized else "draft"))
    return ToolDescriptor(
        tool_id=tool_id,
        version=version,
        description=description,
        entrypoint=dict(entrypoint),
        platforms=[str(p) for p in platforms],
        side_effect_class=side_effect,
        lifecycle_state=lifecycle,
        schema_version=str(raw.get("schema_version") or "0.1"),
        source_path=str(raw.get("source_path") or tool_dir),
        source_hash=raw.get("source_hash"),
        bundle_hash=raw.get("bundle_hash"),
        display_name=raw.get("display_name"),
        input_schema=dict(raw.get("input_schema") or {}),
        output_schema=dict(raw.get("output_schema") or {}),
        timeout_seconds=float(raw["timeout_seconds"]) if raw.get("timeout_seconds") is not None else None,
        raw=dict(raw),
        synthesized=synthesized,
    )


def load_tool_descriptor(tool_dir: Union[str, Path]) -> ToolDescriptor:
    """Load/normalize a tool descriptor from tools/<id>/.

    Preference order:
    1. descriptor.yaml / descriptor.yml
    2. package.json (tool metadata fields)
    3. TOOL.md
    4. synthesize minimal draft from folder name (side_effect_class=unknown)
    """
    path = Path(tool_dir).resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"tool directory not found: {path}")

    descriptor_yaml = path / "descriptor.yaml"
    descriptor_yml = path / "descriptor.yml"
    package_json = path / "package.json"
    tool_md = path / "TOOL.md"

    if descriptor_yaml.is_file():
        return _normalize(_read_yaml_or_json(descriptor_yaml), tool_dir=path)
    if descriptor_yml.is_file():
        return _normalize(_read_yaml_or_json(descriptor_yml), tool_dir=path)
    if package_json.is_file():
        data = _read_yaml_or_json(package_json)
        # Map common npm-ish fields into descriptor shape.
        mapped = {
            "tool_id": data.get("tool_id") or data.get("name") or path.name,
            "version": data.get("version") or "0.0.0-draft",
            "description": data.get("description") or f"Tool {path.name}",
            "entrypoint": data.get("entrypoint")
            or {
                "transport": "cli",
                "command": data.get("bin") if isinstance(data.get("bin"), str) else path.name,
                "working_directory": str(path),
            },
            "platforms": data.get("platforms") or ["any"],
            "side_effect_class": data.get("side_effect_class") or "unknown",
            "lifecycle_state": data.get("lifecycle_state") or "draft",
            "bundle_hash": data.get("bundle_hash"),
            "source_hash": data.get("source_hash"),
        }
        if isinstance(data.get("linkskills"), dict):
            mapped.update(data["linkskills"])
        return _normalize(mapped, tool_dir=path)
    if tool_md.is_file():
        data = _parse_tool_md(tool_md)
        data.setdefault("tool_id", path.name)
        data.setdefault("description", f"Tool {path.name}")
        data.setdefault("side_effect_class", "unknown")
        return _normalize(data, tool_dir=path)

    # Synthesize minimal draft descriptor from folder name.
    return _normalize(
        {
            "tool_id": path.name,
            "version": "0.0.0-draft",
            "description": f"Synthesized draft descriptor for {path.name}",
            "side_effect_class": "unknown",
            "lifecycle_state": "draft",
            "entrypoint": _infer_entrypoint(path, path.name),
            "platforms": ["any"],
        },
        tool_dir=path,
        synthesized=True,
    )
