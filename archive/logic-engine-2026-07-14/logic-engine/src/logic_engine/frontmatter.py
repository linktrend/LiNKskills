from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:idx].rstrip()
    return line.rstrip()


def parse_yaml_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip() for p in inner.split(",")]
        return [parse_yaml_scalar(part) for part in parts]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.match(r"^-?\\d+$", value):
        return int(value)
    if re.match(r"^-?\\d+\\.\\d+$", value):
        return float(value)
    return value


def parse_simple_yaml(text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = strip_yaml_comment(raw)
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"Line {line_no}: missing ':'")
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            errors.append(f"Line {line_no}: indentation must be multiple of 2")
            continue

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            errors.append(f"Line {line_no}: invalid indentation")
            stack = [(-1, root)]
            continue

        parent = stack[-1][1]
        stripped = line.lstrip(" ")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"Line {line_no}: empty key")
            continue

        if value == "":
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_yaml_scalar(value)

    if errors:
        return None, errors
    return root, []


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["Frontmatter opening delimiter not found"]

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break

    if end_idx is None:
        return None, ["Frontmatter closing delimiter not found"]

    raw = "\n".join(lines[1:end_idx])
    return parse_simple_yaml(raw)
