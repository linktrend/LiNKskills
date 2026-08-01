#!/usr/bin/env python3
"""Audit tools/*/ packages for Phase 1 readiness findings."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "evidence" / "phase1" / "tool-audit.json"


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def audit_tool(tool_dir: Path) -> dict[str, Any]:
    tool_id = tool_dir.name
    interface_path = tool_dir / "interface.json"
    readme_path = tool_dir / "README.md"
    bin_dir = tool_dir / "bin"
    test_dir = tool_dir / "test"

    finding: dict[str, Any] = {
        "tool_id": tool_id,
        "path": str(tool_dir.relative_to(REPO_ROOT)),
        "has_interface_json": interface_path.is_file(),
        "has_readme": readme_path.is_file(),
        "has_bin": bin_dir.is_dir(),
        "has_test": test_dir.is_dir(),
        "bin_entries": [],
        "interface_parse_ok": False,
        "interface_name": None,
        "interface_description": None,
        "command_count": 0,
        "parameter_count": 0,
        "readiness": "not_ready",
        "issues": [],
    }

    if bin_dir.is_dir():
        finding["bin_entries"] = sorted(
            p.name for p in bin_dir.iterdir() if p.is_file() or p.is_symlink()
        )

    if not finding["has_interface_json"]:
        finding["issues"].append("missing interface.json")
    else:
        try:
            doc = _load_json(interface_path)
        except Exception as exc:  # noqa: BLE001
            finding["issues"].append(f"interface_json_parse_error: {exc}")
            doc = None
        if isinstance(doc, dict):
            finding["interface_parse_ok"] = True
            finding["interface_name"] = doc.get("name")
            finding["interface_description"] = doc.get("description")
            commands = doc.get("commands") or doc.get("mcp_tools") or []
            params = doc.get("parameters") or []
            finding["command_count"] = len(commands) if isinstance(commands, list) else 0
            finding["parameter_count"] = len(params) if isinstance(params, list) else 0
            if not finding["interface_name"]:
                finding["issues"].append("interface missing name")
            if not finding["interface_description"]:
                finding["issues"].append("interface missing description")
        elif doc is not None:
            finding["issues"].append("interface.json root must be object")

    if not finding["has_readme"]:
        finding["issues"].append("missing README.md")
    if not finding["has_bin"]:
        finding["issues"].append("missing bin/")
    elif not finding["bin_entries"]:
        finding["issues"].append("bin/ is empty")
    if not finding["has_test"]:
        finding["issues"].append("missing test/")

    if (
        finding["interface_parse_ok"]
        and finding["has_readme"]
        and finding["has_bin"]
        and finding["bin_entries"]
        and finding["has_test"]
    ):
        finding["readiness"] = "package_complete"
    elif finding["interface_parse_ok"] and finding["has_bin"]:
        finding["readiness"] = "partial"
    else:
        finding["readiness"] = "not_ready"
    return finding


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    out = Path(argv[0]) if argv else DEFAULT_OUT
    tools_root = REPO_ROOT / "tools"
    findings = []
    for path in sorted(tools_root.iterdir()):
        if not path.is_dir() or path.name.startswith(".") or path.name == "README.md":
            continue
        # Skip non-package files accidentally present as dirs only.
        findings.append(audit_tool(path))

    summary = {
        "schema_version": "0.1",
        "tool_count": len(findings),
        "package_complete": sum(1 for f in findings if f["readiness"] == "package_complete"),
        "partial": sum(1 for f in findings if f["readiness"] == "partial"),
        "not_ready": sum(1 for f in findings if f["readiness"] == "not_ready"),
        "with_interface_json": sum(1 for f in findings if f["has_interface_json"]),
        "with_tests": sum(1 for f in findings if f["has_test"]),
    }
    report = {"summary": summary, "findings": findings}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} ({summary['tool_count']} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
