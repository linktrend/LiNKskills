#!/usr/bin/env python3
"""
Automated validator for skill compliance with the Golden Template.
Enforces frontmatter compliance, naming conventions, file integrity,
contract integrity, persistence/resumability rules, line budgets,
and global tool package compliance under /tools.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASK_ID_REGEX_DEFAULT = r"^\d{8}-\d{4}-[A-Z0-9]+-\d{6}$"

DEFAULT_CONFIG = {
    "logging": {
        "ledger_path": "execution_ledger.jsonl",
        "retention_days": 90,
    },
    "persistence": {
        "root_task_dir": ".workdir/tasks",
    },
    "security": {
        "strict_mode": True,
        "allowed_permissions": ["fs_read", "fs_write", "email_send", "api_access", "shell_exec"],
        "task_id_regex": TASK_ID_REGEX_DEFAULT,
    },
    "engine": {
        "tier_order": ["fast", "balanced", "high"],
        "model_map": {
            "fast": "gpt-4o-mini",
            "balanced": "gpt-4.1",
            "high": "gpt-5",
        },
        "environment": {
            "reasoning_tier": "high",
            "model": "gpt-5",
            "context_window": 200000,
        },
    },
    "tooling": {
        "policy": "cli-first",
        "jit_tool_threshold": 10,
        "require_get_tool_details": True,
    },
}

FRONTMATTER_SCHEMA = {
    "required": [
        "name",
        "description",
        "usage_trigger",
        "version",
        "release_tag",
        "engine",
        "tooling",
        "persistence",
    ],
    "allowed_keys": {
        "name",
        "description",
        "usage_trigger",
        "version",
        "release_tag",
        "engine",
        "tooling",
        "created",
        "author",
        "tags",
        "tools",
        "dependencies",
        "permissions",
        "scope_out",
        "persistence",
        "last_updated",
    },
}


def strip_yaml_comment(line: str) -> str:
    """Strip inline YAML comments while preserving quoted content."""
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


def parse_inline_array(value: str) -> List[Any]:
    """Parse a YAML inline array like [a, "b", c]."""
    assert value.startswith("[") and value.endswith("]")
    inner = value[1:-1].strip()
    if not inner:
        return []

    tokens: List[str] = []
    current = []
    in_single = False
    in_double = False
    escaped = False

    for char in inner:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
            continue
        if char == "," and not in_single and not in_double:
            tokens.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tokens.append("".join(current).strip())

    return [parse_yaml_scalar(token) for token in tokens if token]


def parse_yaml_scalar(value: str) -> Any:
    """Parse a restricted scalar for this repository's YAML conventions."""
    value = value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        return parse_inline_array(value)
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if re.match(r"^-?\d+$", value):
        return int(value)
    if re.match(r"^-?\d+\.\d+$", value):
        return float(value)
    return value


def parse_simple_yaml(text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Parse a constrained subset of YAML used by this repository.
    Supports:
    - top-level key/value pairs
    - nested maps via indentation
    - inline arrays
    """
    errors: List[str] = []
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = strip_yaml_comment(raw)
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"Line {line_no}: missing ':' separator")
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            errors.append(f"Line {line_no}: indentation must be multiples of 2 spaces")
            continue

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            errors.append(f"Line {line_no}: invalid indentation hierarchy")
            stack = [(-1, root)]
            continue

        parent = stack[-1][1]
        stripped = line.lstrip(" ")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            errors.append(f"Line {line_no}: empty key is not allowed")
            continue
        if key in parent:
            errors.append(f"Line {line_no}: duplicate key '{key}'")
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


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_global_config(repo_root: Path) -> Tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []
    config_path = repo_root / "global_config.yaml"
    config = DEFAULT_CONFIG
    if not config_path.exists():
        warnings.append("global_config.yaml not found; using validator defaults")
        return config, warnings

    parsed, errors = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    if errors or parsed is None:
        warnings.extend([f"global_config.yaml parse warning: {err}" for err in errors])
        warnings.append("Falling back to validator defaults where parsing failed.")
        return config, warnings

    config = deep_merge(DEFAULT_CONFIG, parsed)
    return config, warnings


def normalize_tier_order(raw_tier_order: Any) -> List[str]:
    default = ["fast", "balanced", "high"]
    if not isinstance(raw_tier_order, list):
        return default
    normalized: List[str] = []
    for tier in raw_tier_order:
        if isinstance(tier, str) and tier.strip():
            normalized.append(tier.strip())
    return normalized or default


def validate_engine_block(
    engine_block: Any,
    engine_policy: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    """
    Validate per-skill intelligence floor requirements against global engine policy.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(engine_block, dict):
        return ["Frontmatter key 'engine' must be an object"], warnings

    required_keys = {"min_reasoning_tier", "preferred_model", "context_required"}
    allowed_keys = set(required_keys)
    missing = sorted(required_keys - set(engine_block.keys()))
    if missing:
        errors.append(f"engine is missing required key(s): {missing}")
    unknown = sorted(set(engine_block.keys()) - allowed_keys)
    if unknown:
        errors.append(f"engine has unknown key(s): {unknown}")

    tier_order = normalize_tier_order(engine_policy.get("tier_order"))
    tier_rank = {tier: idx for idx, tier in enumerate(tier_order)}

    min_tier = engine_block.get("min_reasoning_tier")
    preferred_model = engine_block.get("preferred_model")
    context_required = engine_block.get("context_required")

    if not isinstance(min_tier, str) or min_tier not in tier_rank:
        errors.append(
            f"engine.min_reasoning_tier must be one of {tier_order}"
        )
    if not isinstance(preferred_model, str) or not preferred_model.strip():
        errors.append("engine.preferred_model must be a non-empty string")
    if not isinstance(context_required, int) or context_required <= 0:
        errors.append("engine.context_required must be a positive integer (token count)")

    model_map = engine_policy.get("model_map")
    if isinstance(model_map, dict) and isinstance(min_tier, str) and isinstance(preferred_model, str):
        expected_model = model_map.get(min_tier)
        if isinstance(expected_model, str) and expected_model and preferred_model != expected_model:
            warnings.append(
                f"engine.preferred_model '{preferred_model}' differs from global_config engine.model_map['{min_tier}']='{expected_model}'"
            )

    environment = engine_policy.get("environment")
    if isinstance(environment, dict):
        env_tier = environment.get("reasoning_tier")
        env_context = environment.get("context_window")
        if isinstance(env_tier, str):
            if env_tier not in tier_rank:
                warnings.append(
                    f"global_config engine.environment.reasoning_tier '{env_tier}' is not in tier_order {tier_order}"
                )
            elif isinstance(min_tier, str) and min_tier in tier_rank and tier_rank[min_tier] > tier_rank[env_tier]:
                errors.append(
                    f"Intelligence floor unmet: skill requires tier '{min_tier}' but environment is '{env_tier}'"
                )
        if isinstance(context_required, int):
            if isinstance(env_context, int):
                if context_required > env_context:
                    errors.append(
                        f"Intelligence floor unmet: skill requires context {context_required}, environment provides {env_context}"
                    )
            elif env_context is not None:
                warnings.append("global_config engine.environment.context_window should be an integer")
    else:
        warnings.append("global_config is missing engine.environment; runtime intelligence floor checks are limited")

    return errors, warnings


def validate_tooling_block(
    tooling_block: Any,
    tooling_policy: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(tooling_block, dict):
        return ["Frontmatter key 'tooling' must be an object"], warnings

    required_keys = {"policy", "jit_enabled_if", "jit_tool_threshold", "require_get_tool_details"}
    allowed_keys = set(required_keys)
    missing = sorted(required_keys - set(tooling_block.keys()))
    if missing:
        errors.append(f"tooling is missing required key(s): {missing}")
    unknown = sorted(set(tooling_block.keys()) - allowed_keys)
    if unknown:
        errors.append(f"tooling has unknown key(s): {unknown}")

    policy = tooling_block.get("policy")
    if policy != "cli-first":
        errors.append("tooling.policy must be 'cli-first'")

    jit_enabled_if = tooling_block.get("jit_enabled_if")
    if jit_enabled_if != "generalist_or_gt10_tools":
        errors.append("tooling.jit_enabled_if must be 'generalist_or_gt10_tools'")

    threshold = tooling_block.get("jit_tool_threshold")
    if not isinstance(threshold, int) or threshold < 1:
        errors.append("tooling.jit_tool_threshold must be an integer >= 1")

    require_get_tool_details = tooling_block.get("require_get_tool_details")
    if require_get_tool_details is not True:
        errors.append("tooling.require_get_tool_details must be true")

    global_policy = tooling_policy.get("policy")
    if isinstance(global_policy, str) and global_policy and policy != global_policy:
        warnings.append(
            f"tooling.policy '{policy}' differs from global_config tooling.policy '{global_policy}'"
        )

    global_threshold = tooling_policy.get("jit_tool_threshold")
    if isinstance(global_threshold, int) and isinstance(threshold, int) and threshold != global_threshold:
        warnings.append(
            f"tooling.jit_tool_threshold {threshold} differs from global_config tooling.jit_tool_threshold {global_threshold}"
        )

    global_require = tooling_policy.get("require_get_tool_details")
    if isinstance(global_require, bool) and isinstance(require_get_tool_details, bool):
        if require_get_tool_details != global_require:
            warnings.append(
                "tooling.require_get_tool_details differs from global_config tooling.require_get_tool_details"
            )

    return errors, warnings


def validate_skill_protocol_content(skill_path: Path, frontmatter: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that SKILL.md body encodes key protocol requirements.
    """
    errors: List[str] = []
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8").lower()

    # Tooling protocol cues
    required_terms = [
        "native cli",
        "cli wrapper",
        "direct api",
        "mcp",
        "state.jsonl",
        "specialist",
        "generalist",
    ]
    for term in required_terms:
        if term not in content:
            errors.append(f"SKILL.md is missing protocol guidance term: '{term}'")

    tooling = frontmatter.get("tooling", {})
    require_get_tool_details = isinstance(tooling, dict) and tooling.get("require_get_tool_details") is True
    if require_get_tool_details and "get_tool_details" not in content:
        errors.append("SKILL.md must reference 'get_tool_details' when tooling.require_get_tool_details is true")

    return len(errors) == 0, errors


def extract_frontmatter(content: str) -> Tuple[Optional[str], List[str], List[str]]:
    """
    Return (frontmatter_text, body_lines, errors) for markdown content.
    """
    errors: List[str] = []
    if not content.startswith("---"):
        return None, [], ["SKILL.md must start with YAML frontmatter (---)"]

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [], ["Frontmatter opening delimiter must be on its own line ('---')."]

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return None, [], ["SKILL.md frontmatter must be closed with ---"]

    frontmatter_text = "\n".join(lines[1:end_idx])
    body_lines = lines[end_idx + 1 :]
    return frontmatter_text, body_lines, errors


def validate_skill_structure(skill_path: Path) -> Tuple[bool, List[str]]:
    """Validate that a skill folder adheres to the Golden Template structure."""
    errors: List[str] = []

    required_files = {
        "SKILL.md": "Core instructions file",
        "advanced/advanced.md": "Advanced logic file",
        "examples/success-pattern.md": "Success pattern example",
        "examples/error-recovery.md": "Error recovery example",
        "references/schemas.json": "JSON schemas",
        "references/api-specs.md": "API specifications",
        "references/old-patterns.md": "Old patterns blacklist",
        "references/changelog.md": "Skill changelog",
        "scripts/helper_tool.py": "Helper utility script",
        "scripts/README.md": "Scripts guide",
        ".gitignore": "Skill-local ignore file",
    }
    required_dirs = {
        ".workdir/tasks": "Persistent task checkpoint directory",
    }

    for rel_path, description in required_files.items():
        full_path = skill_path / rel_path
        if not full_path.is_file():
            errors.append(f"Missing required file: {rel_path} ({description})")
    for rel_path, description in required_dirs.items():
        full_path = skill_path / rel_path
        if not full_path.is_dir():
            errors.append(f"Missing required directory: {rel_path} ({description})")

    return len(errors) == 0, errors


def validate_naming(skill_name: str) -> Tuple[bool, List[str]]:
    """Validate skill name follows kebab-case convention."""
    errors: List[str] = []
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", skill_name):
        errors.append(
            f"Skill name '{skill_name}' must be in kebab-case (lowercase letters, numbers, and hyphens only)"
        )
    return len(errors) == 0, errors


def validate_tool_interface_json(tool_path: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    interface_path = tool_path / "interface.json"
    if not interface_path.exists():
        return False, ["interface.json not found"]
    try:
        payload = json.loads(interface_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"interface.json invalid JSON: {exc}"]

    if not isinstance(payload, dict):
        return False, ["interface.json root must be an object"]

    required_keys = {"name", "description", "capability_summary", "parameters"}
    missing = sorted(required_keys - set(payload.keys()))
    if missing:
        errors.append(f"interface.json missing required keys: {missing}")

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("interface.json.name must be a non-empty string")
    elif name != tool_path.name:
        errors.append(f"interface.json.name '{name}' must match tool directory '{tool_path.name}'")

    description = payload.get("description")
    capability_summary = payload.get("capability_summary")
    if not isinstance(description, str) or len(description.strip()) < 10:
        errors.append("interface.json.description must be a meaningful string (>=10 chars)")
    if not isinstance(capability_summary, str) or len(capability_summary.strip()) < 10:
        errors.append("interface.json.capability_summary must be a meaningful string (>=10 chars)")

    parameters = payload.get("parameters")
    if not isinstance(parameters, list):
        errors.append("interface.json.parameters must be an array")
    else:
        for idx, item in enumerate(parameters):
            if not isinstance(item, dict):
                errors.append(f"interface.json.parameters[{idx}] must be an object")
                continue
            for key in ("name", "type", "description"):
                if key not in item:
                    errors.append(f"interface.json.parameters[{idx}] missing key '{key}'")
                elif not isinstance(item.get(key), str) or not item.get(key).strip():
                    errors.append(f"interface.json.parameters[{idx}].{key} must be a non-empty string")

    return len(errors) == 0, errors


def validate_tool_structure(tool_path: Path) -> Tuple[bool, List[str]]:
    """Validate a global tool package under /tools/[tool-name]."""
    errors: List[str] = []

    _, name_errors = validate_naming(tool_path.name)
    errors.extend([err.replace("Skill name", "Tool name") for err in name_errors])

    required_files = {
        "README.md": "Human-readable docs with capability summary",
        "interface.json": "Tool-calling schema contract",
    }
    required_dirs = {
        "bin": "CLI wrapper executables",
        "test": "Validation scripts",
    }
    for rel_path, desc in required_files.items():
        if not (tool_path / rel_path).is_file():
            errors.append(f"Missing required file: {rel_path} ({desc})")
    for rel_path, desc in required_dirs.items():
        if not (tool_path / rel_path).is_dir():
            errors.append(f"Missing required directory: {rel_path} ({desc})")

    readme_path = tool_path / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8").lower()
        if "capability summary" not in readme:
            errors.append("README.md must include a 'Capability Summary' section for planning/JIT.")
        for flag in ("--help", "--version", "--json"):
            if flag not in readme:
                errors.append(f"README.md should document required CLI flag '{flag}'")

    _, interface_errors = validate_tool_interface_json(tool_path)
    errors.extend(interface_errors)

    bin_dir = tool_path / "bin"
    if bin_dir.exists():
        executables = [p for p in bin_dir.iterdir() if p.is_file()]
        if not executables:
            errors.append("bin/ must contain at least one executable wrapper script")
    test_dir = tool_path / "test"
    if test_dir.exists():
        tests = [p for p in test_dir.iterdir() if p.is_file()]
        if not tests:
            errors.append("test/ must contain at least one validation script")

    return len(errors) == 0, errors


def validate_skill_md_line_count(skill_path: Path) -> Tuple[bool, List[str]]:
    """Validate SKILL.md body is under 500 lines for context efficiency."""
    errors: List[str] = []
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, ["SKILL.md not found"]

    content = skill_md.read_text(encoding="utf-8")
    _, body_lines, fm_errors = extract_frontmatter(content)
    if fm_errors:
        errors.extend(fm_errors)
        return False, errors
    body_line_count = len(body_lines)
    if body_line_count > 500:
        errors.append(
            f"SKILL.md body exceeds 500 lines ({body_line_count} lines). Reduce content for context efficiency."
        )
    return len(errors) == 0, errors


def validate_frontmatter(
    skill_path: Path,
    strict_mode: bool,
    allowed_permissions: List[str],
    root_task_dir: str,
    engine_policy: Dict[str, Any],
    tooling_policy: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], List[str], List[str]]:
    """Validate SKILL.md YAML frontmatter using schema-based key/type/pattern checks."""
    errors: List[str] = []
    warnings: List[str] = []
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None, ["SKILL.md not found"], []

    content = skill_md.read_text(encoding="utf-8")
    frontmatter_text, _, fm_errors = extract_frontmatter(content)
    if fm_errors or frontmatter_text is None:
        return None, fm_errors, []

    frontmatter, parse_errors = parse_simple_yaml(frontmatter_text)
    if parse_errors or frontmatter is None:
        return None, [f"Frontmatter parse error: {err}" for err in parse_errors], []

    required_keys = FRONTMATTER_SCHEMA["required"]
    for key in required_keys:
        if key not in frontmatter:
            errors.append(f"Missing required frontmatter key: {key}")

    if strict_mode:
        allowed_keys = FRONTMATTER_SCHEMA["allowed_keys"]
        for key in frontmatter.keys():
            if key not in allowed_keys:
                errors.append(f"Unknown frontmatter key: {key} (strict mode enabled)")

    name = frontmatter.get("name")
    if not isinstance(name, str):
        errors.append("Frontmatter key 'name' must be a string")
    else:
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name):
            errors.append("Frontmatter key 'name' must be kebab-case")
        if name != skill_path.name:
            errors.append(
                f"Frontmatter name '{name}' must match folder name '{skill_path.name}'"
            )

    description = frontmatter.get("description")
    usage_trigger = frontmatter.get("usage_trigger")
    if not isinstance(description, str) or len(description.strip()) < 10:
        errors.append("Frontmatter key 'description' must be a meaningful string (>=10 chars)")
    if not isinstance(usage_trigger, str) or not usage_trigger.strip():
        errors.append("Frontmatter key 'usage_trigger' must be a non-empty string")

    version = frontmatter.get("version")
    release_tag = frontmatter.get("release_tag")
    if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+$", version):
        errors.append("Frontmatter key 'version' must use semantic version format, e.g. 1.0.0")
    if not isinstance(release_tag, str) or not re.match(r"^v\d+\.\d+\.\d+$", release_tag):
        errors.append("Frontmatter key 'release_tag' must use tag format, e.g. v1.0.0")
    elif isinstance(version, str) and release_tag != f"v{version}":
        errors.append("Frontmatter 'release_tag' must equal 'v' + version")

    tools = frontmatter.get("tools")
    if not isinstance(tools, list) or not tools:
        errors.append("Frontmatter key 'tools' must be a non-empty array")
    else:
        if not all(isinstance(item, str) and item.strip() for item in tools):
            errors.append("Frontmatter key 'tools' must contain only non-empty strings")
        for required_tool in ("write_file", "read_file"):
            if required_tool not in tools:
                errors.append(f"Frontmatter tools must include '{required_tool}'")

    permissions = frontmatter.get("permissions", [])
    if permissions is not None:
        if not isinstance(permissions, list):
            errors.append("Frontmatter key 'permissions' must be an array")
        else:
            for permission in permissions:
                if not isinstance(permission, str):
                    errors.append("Frontmatter permissions values must be strings")
                    continue
                if permission not in allowed_permissions:
                    errors.append(
                        f"Permission '{permission}' is not allowed by global_config.yaml security.allowed_permissions"
                    )

    persistence = frontmatter.get("persistence")
    if not isinstance(persistence, dict):
        errors.append("Frontmatter key 'persistence' must be an object")
    else:
        required_flag = persistence.get("required")
        state_path = persistence.get("state_path")
        if required_flag is not True:
            errors.append("persistence.required must be true for production-grade skills")
        if not isinstance(state_path, str):
            errors.append("persistence.state_path must be a string")
        else:
            if "{{task_id}}" not in state_path:
                errors.append("persistence.state_path must include '{{task_id}}' for resumability")
            if not (state_path.endswith("state.json") or state_path.endswith("state.jsonl")):
                errors.append("persistence.state_path must end with 'state.json' or 'state.jsonl'")
            if root_task_dir and not state_path.startswith(root_task_dir):
                errors.append(
                    f"persistence.state_path must start with '{root_task_dir}' from global_config.yaml"
                )

    engine_errors, engine_warnings = validate_engine_block(frontmatter.get("engine"), engine_policy)
    errors.extend(engine_errors)
    warnings.extend(engine_warnings)

    tooling_errors, tooling_warnings = validate_tooling_block(frontmatter.get("tooling"), tooling_policy)
    errors.extend(tooling_errors)
    warnings.extend(tooling_warnings)

    return frontmatter, errors, warnings


def load_schemas(skill_path: Path) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    schemas_path = skill_path / "references" / "schemas.json"
    if not schemas_path.exists():
        return None, ["references/schemas.json not found"]

    try:
        schema_doc = json.loads(schemas_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"references/schemas.json is not valid JSON: {exc}"]

    if not isinstance(schema_doc, dict):
        errors.append("references/schemas.json root must be an object")
        return None, errors
    definitions = schema_doc.get("definitions")
    if not isinstance(definitions, dict) or not definitions:
        errors.append("references/schemas.json must include a non-empty 'definitions' object")
    if "state" not in definitions:
        errors.append("references/schemas.json definitions must include 'state'")

    return schema_doc, errors


def resolve_json_pointer(doc: Dict[str, Any], pointer: str) -> Optional[Any]:
    if not pointer.startswith("#/"):
        return None
    tokens = pointer[2:].split("/")
    current: Any = doc
    for token in tokens:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        else:
            return None
    return current


def extract_schema_pointers(skill_md_content: str) -> List[str]:
    pattern = re.compile(r"schemas\.json(#[^\s\)`|]+)")
    return sorted(set(pattern.findall(skill_md_content)))


def validate_contract_pointers(skill_path: Path, schema_doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    skill_md = skill_path / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    pointers = extract_schema_pointers(content)
    if not pointers:
        errors.append("No schema contract pointers found in SKILL.md")
        return False, errors

    for pointer in pointers:
        if not pointer.startswith("#/"):
            errors.append(
                f"Invalid schema pointer '{pointer}' in SKILL.md. Use JSON Pointer format like '#/definitions/state'."
            )
            continue
        if resolve_json_pointer(schema_doc, pointer) is None:
            errors.append(f"Schema pointer '{pointer}' in SKILL.md does not exist in references/schemas.json")

    return len(errors) == 0, errors


def validate_value_against_schema(value: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    expected_type = schema.get("type")
    enum_values = schema.get("enum")

    if enum_values is not None and value not in enum_values:
        errors.append(f"{path}: value '{value}' is not one of {enum_values}")

    if expected_type == "object":
        if not isinstance(value, dict):
            return [f"{path}: expected object, got {type(value).__name__}"]
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required key '{key}'")
        for key, item_value in value.items():
            item_schema = properties.get(key)
            if item_schema:
                errors.extend(validate_value_against_schema(item_value, item_schema, f"{path}.{key}"))
    elif expected_type == "array":
        if not isinstance(value, list):
            return [f"{path}: expected array, got {type(value).__name__}"]
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_value_against_schema(item, items_schema, f"{path}[{index}]"))
    elif expected_type == "string":
        if not isinstance(value, str):
            return [f"{path}: expected string, got {type(value).__name__}"]
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path}: string length must be >= {min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.match(pattern, value):
            errors.append(f"{path}: value '{value}' does not match pattern '{pattern}'")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            return [f"{path}: expected integer, got {type(value).__name__}"]
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, int) and value < minimum:
            errors.append(f"{path}: value {value} is less than minimum {minimum}")
        if isinstance(maximum, int) and value > maximum:
            errors.append(f"{path}: value {value} is greater than maximum {maximum}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            return [f"{path}: expected boolean, got {type(value).__name__}"]

    return errors


def validate_runtime_state(
    skill_path: Path,
    state_schema: Optional[Dict[str, Any]],
    task_id_regex: str,
    state_filename: str,
) -> Tuple[bool, List[str]]:
    """
    Validate runtime checkpoint/resumability artifacts.
    - If task folders exist, each must have configured state file and trace.log.
    - state payload must satisfy schema and Task ID format.
    """
    errors: List[str] = []
    tasks_dir = skill_path / ".workdir" / "tasks"
    if not tasks_dir.exists():
        errors.append("Missing .workdir/tasks directory for resumability")
        return False, errors

    task_dirs = [path for path in tasks_dir.iterdir() if path.is_dir()]
    for task_dir in task_dirs:
        state_file = task_dir / state_filename
        trace_file = task_dir / "trace.log"
        if not state_file.exists():
            errors.append(f"{task_dir}: missing {state_filename} (checkpoint required for resumability)")
            continue
        if not trace_file.exists():
            errors.append(f"{task_dir}: missing trace.log (trace logging required)")

        state_payload: Optional[Dict[str, Any]] = None
        if state_filename.endswith(".jsonl"):
            records: List[Dict[str, Any]] = []
            with state_file.open("r", encoding="utf-8") as handle:
                for line_no, raw_line in enumerate(handle, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as exc:
                        errors.append(f"{state_file}:{line_no} invalid JSONL record ({exc})")
                        continue
                    if isinstance(obj, dict):
                        records.append(obj)
                    else:
                        errors.append(f"{state_file}:{line_no} JSONL record must be an object")
            if not records:
                errors.append(f"{state_file}: must contain at least one JSON object record")
                continue
            state_payload = records[-1]
        else:
            try:
                loaded = json.loads(state_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{state_file}: invalid JSON ({exc})")
                continue
            if not isinstance(loaded, dict):
                errors.append(f"{state_file}: JSON root must be an object")
                continue
            state_payload = loaded

        task_id = state_payload.get("task_id")
        if not isinstance(task_id, str):
            errors.append(f"{state_file}: 'task_id' must be a string")
        elif not re.match(task_id_regex, task_id):
            errors.append(
                f"{state_file}: task_id '{task_id}' does not match required pattern '{task_id_regex}'"
            )

        if state_schema is not None:
            schema_errors = validate_value_against_schema(state_payload, state_schema, "$state")
            errors.extend([f"{state_file}: {err}" for err in schema_errors])

    return len(errors) == 0, errors


def parse_iso8601(timestamp: str) -> Optional[datetime]:
    try:
        if timestamp.endswith("Z"):
            timestamp = timestamp.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def validate_execution_ledger(
    repo_root: Path,
    ledger_path: str,
    retention_days: int,
    task_id_regex: str,
) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    ledger_file = repo_root / ledger_path
    if not ledger_file.exists():
        errors.append(f"Ledger file '{ledger_path}' not found (from global_config.yaml logging.ledger_path)")
        return False, errors, warnings

    now = datetime.now(timezone.utc)
    required_fields = {"timestamp", "skill", "task_id", "status", "summary"}
    with ledger_file.open("r", encoding="utf-8") as handle:
        for idx, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{ledger_path}:{idx} invalid JSON: {exc}")
                continue

            missing = sorted(required_fields - set(payload.keys()))
            if missing:
                errors.append(f"{ledger_path}:{idx} missing required fields: {missing}")
                continue

            task_id = payload.get("task_id")
            if not isinstance(task_id, str) or not re.match(task_id_regex, task_id):
                errors.append(
                    f"{ledger_path}:{idx} task_id '{task_id}' does not match required pattern '{task_id_regex}'"
                )

            timestamp_raw = payload.get("timestamp")
            if not isinstance(timestamp_raw, str):
                errors.append(f"{ledger_path}:{idx} timestamp must be a string in ISO 8601 format")
            else:
                parsed = parse_iso8601(timestamp_raw)
                if parsed is None:
                    errors.append(f"{ledger_path}:{idx} invalid ISO 8601 timestamp '{timestamp_raw}'")
                elif retention_days > 0 and (now - parsed).days > retention_days:
                    warnings.append(
                        f"{ledger_path}:{idx} is older than retention_days={retention_days} ({timestamp_raw})"
                    )

    return len(errors) == 0, errors, warnings


def discover_skill_dirs(skills_root: Path) -> List[Path]:
    if not skills_root.exists():
        return []
    discovered = {path.parent.resolve() for path in skills_root.rglob("SKILL.md")}
    return sorted(discovered)


def discover_tool_dirs(tools_root: Path) -> List[Path]:
    if not tools_root.exists():
        return []
    # Tools are defined at /tools/[tool-name]. Nested directories under a tool
    # (for example src/, venv/, __pycache__/) must not be treated as separate tools.
    discovered = [candidate.resolve() for candidate in sorted(tools_root.iterdir()) if candidate.is_dir()]
    return discovered


def validate_single_skill(
    skill_path: Path,
    repo_root: Path,
    config: Dict[str, Any],
    strict_override: Optional[bool],
) -> Tuple[List[str], List[str]]:
    all_errors: List[str] = []
    all_warnings: List[str] = []

    strict_mode = config["security"].get("strict_mode", True)
    if strict_override is not None:
        strict_mode = strict_override
    allowed_permissions = config["security"].get("allowed_permissions", [])
    root_task_dir = config["persistence"].get("root_task_dir", ".workdir/tasks")
    task_id_regex = config["security"].get("task_id_regex", TASK_ID_REGEX_DEFAULT)
    engine_policy = config.get("engine", {})
    tooling_policy = config.get("tooling", {})

    _, errors = validate_naming(skill_path.name)
    all_errors.extend(errors)

    _, errors = validate_skill_structure(skill_path)
    all_errors.extend(errors)

    _, errors = validate_skill_md_line_count(skill_path)
    all_errors.extend(errors)

    frontmatter, errors, frontmatter_warnings = validate_frontmatter(
        skill_path=skill_path,
        strict_mode=bool(strict_mode),
        allowed_permissions=allowed_permissions if isinstance(allowed_permissions, list) else [],
        root_task_dir=str(root_task_dir),
        engine_policy=engine_policy if isinstance(engine_policy, dict) else {},
        tooling_policy=tooling_policy if isinstance(tooling_policy, dict) else {},
    )
    all_errors.extend(errors)
    all_warnings.extend(frontmatter_warnings)

    schema_doc, errors = load_schemas(skill_path)
    all_errors.extend(errors)

    state_schema: Optional[Dict[str, Any]] = None
    if schema_doc is not None:
        _, pointer_errors = validate_contract_pointers(skill_path, schema_doc)
        all_errors.extend(pointer_errors)
        definitions = schema_doc.get("definitions", {})
        state_schema_candidate = definitions.get("state")
        if isinstance(state_schema_candidate, dict):
            state_schema = state_schema_candidate

    state_filename = "state.json"
    if isinstance(frontmatter, dict):
        persistence = frontmatter.get("persistence")
        if isinstance(persistence, dict):
            state_path = persistence.get("state_path")
            if isinstance(state_path, str):
                state_filename = Path(state_path).name

    if isinstance(frontmatter, dict):
        _, protocol_errors = validate_skill_protocol_content(skill_path, frontmatter)
        all_errors.extend(protocol_errors)

    _, errors = validate_runtime_state(skill_path, state_schema, task_id_regex, state_filename)
    all_errors.extend(errors)

    return all_errors, all_warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate skill compliance with the LiNKskills Golden Template"
    )
    parser.add_argument(
        "--path",
        required=False,
        help="Path to a skill folder (/skills/*) or tool folder (/tools/*). If omitted with --scan-all, validates entire registry.",
    )
    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Recursively validate all skills under /skills and all tools under /tools",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path containing global_config.yaml and execution_ledger.jsonl",
    )
    parser.add_argument(
        "--strict",
        dest="strict_override",
        action="store_true",
        default=None,
        help="Override global_config strict_mode to true",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict_override",
        action="store_false",
        help="Override global_config strict_mode to false",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    config, config_warnings = load_global_config(repo_root)
    ledger_path = config["logging"].get("ledger_path", "execution_ledger.jsonl")
    retention_days = config["logging"].get("retention_days", 0)
    task_id_regex = config["security"].get("task_id_regex", TASK_ID_REGEX_DEFAULT)

    all_errors: List[str] = []
    all_warnings: List[str] = list(config_warnings)

    processed_labels: List[str] = []
    if args.scan_all:
        skills_root = repo_root / "skills"
        tools_root = repo_root / "tools"
        skill_dirs = discover_skill_dirs(skills_root)
        tool_dirs = discover_tool_dirs(tools_root)

        if not skills_root.exists():
            all_errors.append("Missing required /skills directory at repository root")
        if not tools_root.exists():
            all_errors.append("Missing required /tools directory at repository root")
        if not skill_dirs:
            all_errors.append("No skills found under /skills")

        for skill_dir in skill_dirs:
            errors, warnings = validate_single_skill(
                skill_path=skill_dir,
                repo_root=repo_root,
                config=config,
                strict_override=args.strict_override,
            )
            processed_labels.append(f"skill:{skill_dir.relative_to(repo_root)}")
            all_errors.extend([f"{skill_dir.relative_to(repo_root)}: {err}" for err in errors])
            all_warnings.extend([f"{skill_dir.relative_to(repo_root)}: {warn}" for warn in warnings])

        for tool_dir in tool_dirs:
            _, errors = validate_tool_structure(tool_dir)
            processed_labels.append(f"tool:{tool_dir.relative_to(repo_root)}")
            all_errors.extend([f"{tool_dir.relative_to(repo_root)}: {err}" for err in errors])
    else:
        if not args.path:
            print("Error: provide --path or use --scan-all", file=sys.stderr)
            sys.exit(1)
        target_path = Path(args.path)
        if not target_path.is_absolute():
            target_path = (repo_root / target_path).resolve()
        else:
            target_path = target_path.resolve()

        if not target_path.exists():
            print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
            sys.exit(1)
        if not target_path.is_dir():
            print(f"Error: Path '{target_path}' is not a directory", file=sys.stderr)
            sys.exit(1)

        if (target_path / "SKILL.md").exists():
            errors, warnings = validate_single_skill(
                skill_path=target_path,
                repo_root=repo_root,
                config=config,
                strict_override=args.strict_override,
            )
            processed_labels.append(f"skill:{target_path.relative_to(repo_root)}")
            all_errors.extend([f"{target_path.relative_to(repo_root)}: {err}" for err in errors])
            all_warnings.extend([f"{target_path.relative_to(repo_root)}: {warn}" for warn in warnings])
        else:
            _, errors = validate_tool_structure(target_path)
            processed_labels.append(f"tool:{target_path.relative_to(repo_root)}")
            all_errors.extend([f"{target_path.relative_to(repo_root)}: {err}" for err in errors])

    _, ledger_errors, ledger_warnings = validate_execution_ledger(
        repo_root=repo_root,
        ledger_path=str(ledger_path),
        retention_days=int(retention_days) if isinstance(retention_days, int) else 0,
        task_id_regex=str(task_id_regex),
    )
    all_errors.extend(ledger_errors)
    all_warnings.extend(ledger_warnings)

    if all_errors:
        context_label = "registry" if args.scan_all else (processed_labels[0] if processed_labels else "target")
        print(f"Validation failed for '{context_label}':", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        if all_warnings:
            print("Warnings:", file=sys.stderr)
            for warning in all_warnings:
                print(f"  - {warning}", file=sys.stderr)
        sys.exit(1)

    if args.scan_all:
        print(f"✓ Validation passed for registry scan ({len(processed_labels)} targets)")
    else:
        label = processed_labels[0] if processed_labels else "target"
        print(f"✓ Validation passed for '{label}'")
    if all_warnings:
        print("Warnings:")
        for warning in all_warnings:
            print(f"  - {warning}")
    sys.exit(0)

if __name__ == "__main__":
    main()
