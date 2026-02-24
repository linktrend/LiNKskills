# YAML Frontmatter Specification

This document defines the required and optional fields for skill `SKILL.md` frontmatter.

## Required Fields

- **`name`** (string): Skill identifier in kebab-case. Must match folder name.
- **`description`** (string): Third-person summary of what the skill does.
- **`usage_trigger`** (string): Explicit context for when to use this skill.
- **`version`** (string): Semantic version (e.g., "1.0.0").
- **`release_tag`** (string): Version tag format (e.g., "v1.0.0"). Must match `version`.
- **`engine`** (object): Intelligence floor required for reliable execution:
  - `min_reasoning_tier` (string): Required tier, e.g., `fast`, `balanced`, `high`.
  - `preferred_model` (string): Recommended model identifier.
  - `context_required` (integer): Minimum context window in tokens.
- **`tooling`** (object): Global Tooling & Persistence protocol requirements:
  - `policy` (string): Must be `cli-first`.
  - `jit_enabled_if` (string): `generalist_or_gt10_tools`.
  - `jit_tool_threshold` (integer): Activation threshold for JIT (default 10).
  - `require_get_tool_details` (boolean): Must be `true`.

## Optional Fields

- **`created`** (date): ISO 8601 date when skill was created (YYYY-MM-DD).
- **`author`** (string): Studio/Author name.
- **`tags`** (array): Category tags for organization.
- **`tools`** (array): List of tools the skill uses. Must include at least `write_file`, `read_file`.
- **`dependencies`** (array): MCP server IDs or local script paths.
- **`permissions`** (array): Permission scopes (fs_read, fs_write, email_send, api_access, shell_exec).
- **`scope_out`** (array): Explicitly forbidden actions.
- **`persistence`** (object):
  - `required` (boolean): Whether persistence is required.
  - `state_path` (string): Path template for state file (e.g., ".workdir/tasks/{{task_id}}/state.jsonl").
- **`last_updated`** (date): ISO 8601 date of last update.

## Validation Rules

- All field names must be lowercase with underscores (snake_case).
- `name` must be valid kebab-case (lowercase letters, numbers, hyphens only).
- `tools` array must include `write_file` and `read_file`.
- `persistence.required` must be `true` for production-grade skills.
- `persistence.state_path` should default to `.workdir/tasks/{{task_id}}/state.jsonl`.
- `release_tag` must equal `v` + `version`.
- `engine.min_reasoning_tier` must map to a valid tier in `global_config.yaml`.
- `engine.context_required` must be less than or equal to environment context capacity.
- `tooling.policy` must remain `cli-first` unless formally exempted.
- Every skill must maintain `references/changelog.md` for traceable evolution.
